from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import EntidadTipo
from app.paths import DATA_DIR, VIEWER3D_DIR
from app.services import EquipoService, MantenimientoService, Modelo3DService

VIEWER3D_URL_PATH = "index.html"


class _ViewerRequestHandler(SimpleHTTPRequestHandler):
    """Sirve los assets del visor (empaquetados, solo lectura) desde
    VIEWER3D_DIR, y los modelos .glb/.gltf importados por el usuario
    (escribibles, fuera del bundle) desde DATA_DIR bajo el prefijo /data/.
    Ambos árboles pueden vivir en ubicaciones completamente distintas
    cuando la app corre empaquetada (PyInstaller)."""

    def translate_path(self, path: str) -> str:
        path = unquote(path.split("?", 1)[0].split("#", 1)[0])
        if path.startswith("/data/"):
            base, relativa = DATA_DIR, path[len("/data/") :]
        else:
            base, relativa = VIEWER3D_DIR, path.lstrip("/")
        base = base.resolve()
        destino = (base / relativa).resolve()
        if destino != base and base not in destino.parents:
            destino = base
        return str(destino)


def _iniciar_servidor_local() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ViewerRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


class MarcadorBridge(QObject):
    # Python -> JS
    cargar_modelo = Signal(str)
    agregar_marcador = Signal(int, float, float, float, str)
    eliminar_marcador = Signal(int)
    limpiar_marcadores = Signal()
    establecer_modo_agregar = Signal(bool)

    # JS -> Python
    nuevo_marcador_solicitado = Signal(float, float, float)
    marcador_seleccionado = Signal(int)

    @Slot(float, float, float)
    def solicitar_nuevo_marcador(self, x: float, y: float, z: float) -> None:
        self.nuevo_marcador_solicitado.emit(x, y, z)

    @Slot(int)
    def marcador_click(self, marcador_id: int) -> None:
        self.marcador_seleccionado.emit(marcador_id)

    @Slot()
    def modelo_cargado(self) -> None:
        pass


class MarcadorFormDialog(QDialog):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo marcador")
        self.apartamento_id = apartamento_id

        self.etiqueta = QLineEdit()

        self.tipo_referencia = QComboBox()
        self.tipo_referencia.addItem("(ninguno)", None)
        self.tipo_referencia.addItem("Equipo", EntidadTipo.EQUIPO)
        self.tipo_referencia.addItem("Mantenimiento", EntidadTipo.MANTENIMIENTO)
        self.tipo_referencia.currentIndexChanged.connect(self._actualizar_referencias)

        self.referencia = QComboBox()

        form = QFormLayout()
        form.addRow("Etiqueta", self.etiqueta)
        form.addRow("Vincular a", self.tipo_referencia)
        form.addRow("Elemento", self.referencia)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._actualizar_referencias()

    def _actualizar_referencias(self) -> None:
        self.referencia.clear()
        tipo = self.tipo_referencia.currentData()
        if tipo == EntidadTipo.EQUIPO:
            for equipo in EquipoService.listar_por_apartamento(self.apartamento_id):
                self.referencia.addItem(equipo.nombre, equipo.id)
        elif tipo == EntidadTipo.MANTENIMIENTO:
            for mant in MantenimientoService.listar_por_apartamento(self.apartamento_id):
                self.referencia.addItem(mant.titulo, mant.id)
        self.referencia.setEnabled(tipo is not None)

    def _validar_y_aceptar(self) -> None:
        if not self.etiqueta.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "La etiqueta es obligatoria.")
            return
        self.accept()

    def datos(self) -> dict:
        tipo = self.tipo_referencia.currentData()
        return {
            "etiqueta": self.etiqueta.text().strip(),
            "tipo_referencia": tipo,
            "referencia_id": self.referencia.currentData() if tipo is not None else None,
        }


class Viewer3DView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id
        self._server = _iniciar_servidor_local()
        self._port = self._server.server_address[1]

        self.web_view = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = MarcadorBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        self.bridge.nuevo_marcador_solicitado.connect(self._crear_marcador_en)
        self.bridge.marcador_seleccionado.connect(self._mostrar_detalle_marcador)

        btn_importar = QPushButton("Importar modelo (.glb/.gltf)...")
        btn_importar.clicked.connect(self._importar_modelo)

        self.chk_agregar = QCheckBox("Modo agregar marcador")
        self.chk_agregar.toggled.connect(self.bridge.establecer_modo_agregar.emit)

        btn_recargar = QPushButton("Recargar")
        btn_recargar.clicked.connect(self._cargar_todo)

        botones = QHBoxLayout()
        botones.addWidget(btn_importar)
        botones.addWidget(self.chk_agregar)
        botones.addStretch()
        botones.addWidget(btn_recargar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.web_view, 1)

        self.web_view.loadFinished.connect(self._al_cargar_pagina)
        self.web_view.setUrl(self._url(VIEWER3D_URL_PATH))

    def _url(self, ruta_relativa: str) -> QUrl:
        return QUrl(f"http://127.0.0.1:{self._port}/{ruta_relativa}")

    def _al_cargar_pagina(self, ok: bool) -> None:
        if ok:
            self._cargar_todo()

    def _cargar_todo(self) -> None:
        self.bridge.limpiar_marcadores.emit()
        modelo = Modelo3DService.obtener_por_apartamento(self.apartamento_id)
        if modelo is None:
            return
        self.bridge.cargar_modelo.emit(self._url(f"data/{modelo.archivo_modelo}").toString())
        for marcador in Modelo3DService.listar_marcadores(modelo.id):
            self.bridge.agregar_marcador.emit(
                marcador.id, marcador.pos_x, marcador.pos_y, marcador.pos_z, marcador.etiqueta
            )

    def _importar_modelo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar modelo 3D", str(Path.home()), "Modelos 3D (*.glb *.gltf)"
        )
        if not ruta:
            return
        try:
            Modelo3DService.importar_modelo(self.apartamento_id, Path(ruta))
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self._cargar_todo()

    def _crear_marcador_en(self, x: float, y: float, z: float) -> None:
        modelo = Modelo3DService.obtener_por_apartamento(self.apartamento_id)
        if modelo is None:
            return
        dialog = MarcadorFormDialog(self.apartamento_id, self)
        if dialog.exec() != QDialog.Accepted:
            return
        marcador = Modelo3DService.crear_marcador(
            modelo_3d_id=modelo.id, pos_x=x, pos_y=y, pos_z=z, **dialog.datos()
        )
        self.bridge.agregar_marcador.emit(marcador.id, x, y, z, marcador.etiqueta)

    def _mostrar_detalle_marcador(self, marcador_id: int) -> None:
        marcador = Modelo3DService.obtener_marcador(marcador_id)
        if marcador is None:
            return
        detalle = marcador.etiqueta
        if marcador.tipo_referencia is not None:
            detalle += f"\nVinculado a: {marcador.tipo_referencia.value} #{marcador.referencia_id}"
        respuesta = QMessageBox.question(
            self,
            f"Marcador #{marcador.id}",
            detalle + "\n\n¿Eliminar este marcador?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if respuesta == QMessageBox.Yes:
            Modelo3DService.eliminar_marcador(marcador_id)
            self.bridge.eliminar_marcador.emit(marcador_id)
