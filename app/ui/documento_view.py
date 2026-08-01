from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QDate
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models import EntidadTipo, TipoDocumento
from app.models.base import DATA_DIR
from app.services import DocumentoService

COLUMNS = ["ID", "Tipo", "Archivo", "Asociado a", "ID entidad", "Fecha subida"]

DOCUMENTOS_DIR = DATA_DIR / "documentos"
PROJECT_ROOT = DATA_DIR.parent


class DocumentoFormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo documento")
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

        self.entidad_id = QSpinBox()
        self.entidad_id.setRange(1, 999_999)

        self.fecha_subida = QDateEdit(calendarPopup=True)
        self.fecha_subida.setDate(QDate.currentDate())

        form = QFormLayout()
        form.addRow("Tipo de documento", self.tipo)
        form.addRow("Archivo", fila_archivo)
        form.addRow("Asociado a", self.entidad_tipo)
        form.addRow("ID de la entidad", self.entidad_id)
        form.addRow("Fecha de subida", self.fecha_subida)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validar_y_aceptar)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def _seleccionar_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar documento", str(Path.home()), "Documentos (*.pdf *.jpg *.jpeg *.png)"
        )
        if not ruta:
            return
        self._ruta_origen = Path(ruta)
        self.archivo.setText(self._ruta_origen.name)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)

    def _validar_y_aceptar(self) -> None:
        if self._ruta_origen is None:
            QMessageBox.warning(self, "Datos incompletos", "Selecciona un archivo.")
            return
        self.accept()

    def datos(self) -> dict:
        destino = self._copiar_a_documentos(self._ruta_origen)
        return {
            "tipo": self.tipo.currentData(),
            "nombre_archivo": self._ruta_origen.name,
            "ruta_archivo": str(destino.relative_to(PROJECT_ROOT)),
            "entidad_tipo": self.entidad_tipo.currentData(),
            "entidad_id": self.entidad_id.value(),
            "fecha_subida": self.fecha_subida.date().toPython(),
        }

    @staticmethod
    def _copiar_a_documentos(origen: Path) -> Path:
        DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
        destino = DOCUMENTOS_DIR / origen.name
        contador = 1
        while destino.exists():
            destino = DOCUMENTOS_DIR / f"{origen.stem}_{contador}{origen.suffix}"
            contador += 1
        shutil.copy2(origen, destino)
        return destino


class DocumentoView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

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
                str(documento.entidad_id),
                documento.fecha_subida.isoformat(),
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(row, col, QTableWidgetItem(valor))

    def _selected_id(self) -> int | None:
        row = self.tabla.currentRow()
        if row < 0:
            return None
        item = self.tabla.item(row, 0)
        return int(item.text()) if item else None

    def _nuevo(self) -> None:
        dialog = DocumentoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            DocumentoService.crear(**dialog.datos())
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
