from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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

from app.models import Contrato, EntidadTipo, EstadoContrato
from app.services import ContratoService
from app.ui.documento_view import DocumentosDeEntidadDialog

COLUMNS = ["ID", "Inicio", "Fin", "Monto mensual", "Arrendador", "Arrendatario", "Estado"]


class ContratoFormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, contrato: Contrato | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo contrato" if contrato is None else f"Editar contrato #{contrato.id}")

        self.fecha_inicio = QDateEdit(calendarPopup=True)
        self.fecha_inicio.setDate(QDate.currentDate())

        self.fecha_fin = QDateEdit(calendarPopup=True)
        self.fecha_fin.setDate(QDate.currentDate())
        self.sin_fecha_fin = QCheckBox("Sin definir")
        self.sin_fecha_fin.toggled.connect(self.fecha_fin.setDisabled)
        fila_fecha_fin = QHBoxLayout()
        fila_fecha_fin.addWidget(self.fecha_fin)
        fila_fecha_fin.addWidget(self.sin_fecha_fin)

        self.monto_mensual = QDoubleSpinBox()
        self.monto_mensual.setRange(0.01, 10_000_000)
        self.monto_mensual.setDecimals(2)
        self.monto_mensual.setValue(1.0)

        self.arrendador = QLineEdit()
        self.arrendatario = QLineEdit()

        self.estado = QComboBox()
        for estado in EstadoContrato:
            self.estado.addItem(estado.value, estado)

        if contrato is not None:
            fi = contrato.fecha_inicio
            self.fecha_inicio.setDate(QDate(fi.year, fi.month, fi.day))
            if contrato.fecha_fin is not None:
                ff = contrato.fecha_fin
                self.fecha_fin.setDate(QDate(ff.year, ff.month, ff.day))
            else:
                self.sin_fecha_fin.setChecked(True)
            self.monto_mensual.setValue(contrato.monto_mensual)
            self.arrendador.setText(contrato.arrendador)
            self.arrendatario.setText(contrato.arrendatario)
            self.estado.setCurrentIndex(self.estado.findData(contrato.estado))
        else:
            self.sin_fecha_fin.setChecked(True)

        form = QFormLayout()
        form.addRow("Fecha inicio", self.fecha_inicio)
        form.addRow("Fecha fin", fila_fecha_fin)
        form.addRow("Monto mensual", self.monto_mensual)
        form.addRow("Arrendador", self.arrendador)
        form.addRow("Arrendatario", self.arrendatario)
        form.addRow("Estado", self.estado)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if not self.arrendador.text().strip() or not self.arrendatario.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "Arrendador y arrendatario son obligatorios.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "fecha_inicio": self.fecha_inicio.date().toPython(),
            "fecha_fin": None if self.sin_fecha_fin.isChecked() else self.fecha_fin.date().toPython(),
            "monto_mensual": self.monto_mensual.value(),
            "arrendador": self.arrendador.text().strip(),
            "arrendatario": self.arrendatario.text().strip(),
            "estado": self.estado.currentData(),
        }


class ContratoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.tabla = QTableWidget(0, len(COLUMNS))
        self.tabla.setHorizontalHeaderLabels(COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_nuevo = QPushButton("Nuevo")
        btn_editar = QPushButton("Editar")
        btn_documentos = QPushButton("Documentos...")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_documentos.clicked.connect(self._documentos)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_editar)
        botones.addWidget(btn_documentos)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        contratos = ContratoService.listar_por_apartamento(self.apartamento_id)
        self.tabla.setRowCount(0)
        for contrato in contratos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(contrato.id),
                contrato.fecha_inicio.isoformat(),
                contrato.fecha_fin.isoformat() if contrato.fecha_fin else "",
                f"{contrato.monto_mensual:.2f}",
                contrato.arrendador,
                contrato.arrendatario,
                contrato.estado.value,
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
        dialog = ContratoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            ContratoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        contrato_id = self._selected_id()
        if contrato_id is None:
            QMessageBox.information(self, "Editar contrato", "Selecciona un contrato de la tabla.")
            return
        contrato = ContratoService.obtener(contrato_id)
        if contrato is None:
            QMessageBox.warning(self, "Error", "El contrato ya no existe.")
            self.refrescar()
            return
        dialog = ContratoFormDialog(self, contrato)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            ContratoService.actualizar(contrato_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _eliminar(self) -> None:
        contrato_id = self._selected_id()
        if contrato_id is None:
            QMessageBox.information(self, "Eliminar contrato", "Selecciona un contrato de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar contrato", f"¿Eliminar el contrato #{contrato_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        ContratoService.eliminar(contrato_id)
        self.refrescar()

    def _documentos(self) -> None:
        contrato_id = self._selected_id()
        if contrato_id is None:
            QMessageBox.information(self, "Documentos", "Selecciona un contrato de la tabla.")
            return
        contrato = ContratoService.obtener(contrato_id)
        if contrato is None:
            QMessageBox.warning(self, "Error", "El contrato ya no existe.")
            self.refrescar()
            return
        etiqueta = f"Contrato #{contrato.id} ({contrato.arrendador} / {contrato.arrendatario})"
        DocumentosDeEntidadDialog(EntidadTipo.CONTRATO, contrato_id, etiqueta, self).exec()
