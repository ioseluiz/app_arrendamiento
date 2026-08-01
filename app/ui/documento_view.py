from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models import EntidadTipo, TipoDocumento
from app.services import (
    ContratoService,
    DocumentoService,
    EquipoService,
    MantenimientoService,
    PagoService,
)

COLUMNS = ["ID", "Tipo", "Archivo", "Asociado a", "Elemento", "Fecha subida"]


def _opciones_entidad(apartamento_id: int, tipo: EntidadTipo) -> list[tuple[str, int]]:
    """Devuelve pares (etiqueta legible, id) de las entidades existentes de
    ese tipo, para poblar un combo en vez de pedir un ID a mano."""
    if tipo == EntidadTipo.CONTRATO:
        return [
            (f"Contrato #{c.id} ({c.arrendador} / {c.arrendatario})", c.id)
            for c in ContratoService.listar_por_apartamento(apartamento_id)
        ]
    if tipo == EntidadTipo.EQUIPO:
        return [(e.nombre, e.id) for e in EquipoService.listar_por_apartamento(apartamento_id)]
    if tipo == EntidadTipo.MANTENIMIENTO:
        return [(m.titulo, m.id) for m in MantenimientoService.listar_por_apartamento(apartamento_id)]
    if tipo == EntidadTipo.PAGO_SERVICIO:
        return [
            (f"{p.tipo_servicio.value} ({p.periodo})", p.id)
            for p in PagoService.listar_por_apartamento(apartamento_id)
        ]
    return []


class DocumentoFormDialog(QDialog):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id
        self.setWindowTitle("Adjuntar documento")
        self._ruta_origen: Path | None = None

        self.tipo = QComboBox()
        for tipo in TipoDocumento:
            self.tipo.addItem(tipo.value, tipo)

        self.archivo = QLineEdit()
        self.archivo.setReadOnly(True)
        self.archivo.setPlaceholderText("Ningún archivo seleccionado")
        btn_seleccionar = QPushButton("Seleccionar archivo...")
        btn_seleccionar.clicked.connect(self._seleccionar_archivo)
        fila_archivo = QHBoxLayout()
        fila_archivo.addWidget(self.archivo)
        fila_archivo.addWidget(btn_seleccionar)

        self.entidad_tipo = QComboBox()
        for entidad in EntidadTipo:
            self.entidad_tipo.addItem(entidad.value, entidad)

        self.entidad = QComboBox()

        self.fecha_subida = QDateEdit(calendarPopup=True)
        self.fecha_subida.setDate(QDate.currentDate())

        form = QFormLayout()
        form.addRow("Tipo de documento", self.tipo)
        form.addRow("Archivo", fila_archivo)
        form.addRow("Asociado a", self.entidad_tipo)
        form.addRow("Elemento", self.entidad)
        form.addRow("Fecha de subida", self.fecha_subida)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validar_y_aceptar)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        self.entidad_tipo.currentIndexChanged.connect(self._actualizar_entidades)
        self._actualizar_entidades()

    def _actualizar_entidades(self) -> None:
        self.entidad.clear()
        tipo = self.entidad_tipo.currentData()
        for etiqueta, entidad_id in _opciones_entidad(self.apartamento_id, tipo):
            self.entidad.addItem(etiqueta, entidad_id)
        self.entidad.setEnabled(self.entidad.count() > 0)

    def _seleccionar_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar documento", str(Path.home()), "Documentos (*.pdf *.jpg *.jpeg *.png)"
        )
        if not ruta:
            return
        self._ruta_origen = Path(ruta)
        self.archivo.setText(self._ruta_origen.name)

    def _validar_y_aceptar(self) -> None:
        if self._ruta_origen is None:
            QMessageBox.warning(self, "Datos incompletos", "Selecciona un archivo.")
            return
        if self.entidad.count() == 0:
            QMessageBox.warning(
                self,
                "Sin elementos",
                "No hay ningún elemento de ese tipo todavía para vincular el documento. Créalo primero.",
            )
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "entidad_tipo": self.entidad_tipo.currentData(),
            "entidad_id": self.entidad.currentData(),
            "ruta_origen": self._ruta_origen,
            "tipo": self.tipo.currentData(),
            "fecha_subida": self.fecha_subida.date().toPython(),
        }


class DocumentosDeEntidadDialog(QDialog):
    """Diálogo compacto para ver/adjuntar/eliminar documentos de UNA entidad
    puntual (ej. un mantenimiento o un pago), sin pasar por la pestaña
    Documentos ni tener que elegir el elemento otra vez."""

    COLUMNS = ["Tipo", "Archivo", "Fecha subida"]

    def __init__(
        self,
        entidad_tipo: EntidadTipo,
        entidad_id: int,
        etiqueta: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.entidad_tipo = entidad_tipo
        self.entidad_id = entidad_id
        self.setWindowTitle(f"Documentos — {etiqueta}")
        self.resize(480, 320)

        self.tabla = QTableWidget(0, len(self.COLUMNS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_adjuntar = QPushButton("Adjuntar...")
        btn_adjuntar.clicked.connect(self._adjuntar)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        botones = QHBoxLayout()
        botones.addWidget(btn_adjuntar)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_cerrar)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabla)
        layout.addLayout(botones)

        self.refrescar()

    def refrescar(self) -> None:
        documentos = DocumentoService.listar_por_entidad(self.entidad_tipo, self.entidad_id)
        self.tabla.setRowCount(0)
        for documento in documentos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [documento.tipo.value, documento.nombre_archivo, documento.fecha_subida.isoformat()]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.UserRole, documento.id)
                self.tabla.setItem(row, col, item)

    def _selected_id(self) -> int | None:
        row = self.tabla.currentRow()
        if row < 0:
            return None
        item = self.tabla.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _adjuntar(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar documento", str(Path.home()), "Documentos (*.pdf *.jpg *.jpeg *.png)"
        )
        if not ruta:
            return
        DocumentoService.adjuntar(self.entidad_tipo, self.entidad_id, Path(ruta))
        self.refrescar()

    def _eliminar(self) -> None:
        documento_id = self._selected_id()
        if documento_id is None:
            QMessageBox.information(self, "Eliminar documento", "Selecciona un documento de la tabla.")
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar documento",
            "¿Eliminar el registro de este documento?\n(el archivo en disco no se borra)",
        )
        if respuesta != QMessageBox.Yes:
            return
        DocumentoService.eliminar(documento_id)
        self.refrescar()


class DocumentoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.tabla = QTableWidget(0, len(COLUMNS))
        self.tabla.setHorizontalHeaderLabels(COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_nuevo = QPushButton("Adjuntar...")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        documentos = DocumentoService.listar()
        self.tabla.setRowCount(0)
        for documento in documentos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(documento.id),
                documento.tipo.value,
                documento.nombre_archivo,
                documento.entidad_tipo.value,
                self._etiqueta_entidad(documento.entidad_tipo, documento.entidad_id),
                documento.fecha_subida.isoformat(),
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(row, col, QTableWidgetItem(valor))

    def _etiqueta_entidad(self, tipo: EntidadTipo, entidad_id: int) -> str:
        for etiqueta, opcion_id in _opciones_entidad(self.apartamento_id, tipo):
            if opcion_id == entidad_id:
                return etiqueta
        return f"#{entidad_id} (ya no existe)"

    def _selected_id(self) -> int | None:
        row = self.tabla.currentRow()
        if row < 0:
            return None
        item = self.tabla.item(row, 0)
        return int(item.text()) if item else None

    def _nuevo(self) -> None:
        dialog = DocumentoFormDialog(self.apartamento_id, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            DocumentoService.adjuntar(**dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _eliminar(self) -> None:
        documento_id = self._selected_id()
        if documento_id is None:
            QMessageBox.information(self, "Eliminar documento", "Selecciona un documento de la tabla.")
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar documento",
            f"¿Eliminar el registro del documento #{documento_id}?\n"
            "(el archivo en disco no se borra)",
        )
        if respuesta != QMessageBox.Yes:
            return
        DocumentoService.eliminar(documento_id)
        self.refrescar()
