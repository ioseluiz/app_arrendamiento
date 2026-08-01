from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
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

from app.models import EntidadTipo, EstadoPago, PagoServicio, TipoServicio
from app.services import PagoService, ProveedorService
from app.ui.documento_view import DocumentosDeEntidadDialog

COLUMNS = ["ID", "Servicio", "Periodo", "Monto", "Proveedor", "Vencimiento", "Pago", "Estado"]


class PagoFormDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        pago: PagoServicio | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo pago" if pago is None else f"Editar pago #{pago.id}")

        self.proveedor = QComboBox()
        for proveedor in ProveedorService.listar():
            self.proveedor.addItem(proveedor.nombre, proveedor.id)

        self.tipo_servicio = QComboBox()
        for tipo in TipoServicio:
            self.tipo_servicio.addItem(tipo.value, tipo)

        self.periodo = QLineEdit()
        self.periodo.setPlaceholderText("ej. 2026-07")

        self.monto = QDoubleSpinBox()
        self.monto.setRange(0.01, 1_000_000)
        self.monto.setDecimals(2)
        self.monto.setValue(1.0)

        self.fecha_vencimiento = QDateEdit(calendarPopup=True)
        self.fecha_vencimiento.setDate(QDate.currentDate())

        self.estado = QComboBox()
        for estado in EstadoPago:
            self.estado.addItem(estado.value, estado)

        if pago is not None:
            self.proveedor.setCurrentIndex(self.proveedor.findData(pago.proveedor_id))
            self.tipo_servicio.setCurrentIndex(self.tipo_servicio.findData(pago.tipo_servicio))
            self.periodo.setText(pago.periodo)
            self.monto.setValue(pago.monto)
            fv = pago.fecha_vencimiento
            self.fecha_vencimiento.setDate(QDate(fv.year, fv.month, fv.day))
            self.estado.setCurrentIndex(self.estado.findData(pago.estado))

        form = QFormLayout()
        form.addRow("Proveedor", self.proveedor)
        form.addRow("Tipo de servicio", self.tipo_servicio)
        form.addRow("Periodo", self.periodo)
        form.addRow("Monto", self.monto)
        form.addRow("Fecha de vencimiento", self.fecha_vencimiento)
        form.addRow("Estado", self.estado)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if self.proveedor.count() == 0:
            QMessageBox.warning(self, "Sin proveedores", "Crea primero un proveedor en la pestaña Proveedores.")
            self.reject()
            return
        if not self.periodo.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El periodo es obligatorio.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "proveedor_id": self.proveedor.currentData(),
            "tipo_servicio": self.tipo_servicio.currentData(),
            "periodo": self.periodo.text().strip(),
            "monto": self.monto.value(),
            "fecha_vencimiento": self.fecha_vencimiento.date().toPython(),
            "estado": self.estado.currentData(),
        }


class MarcarPagadoDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Marcar como pagado")

        self.fecha_pago = QDateEdit(calendarPopup=True)
        self.fecha_pago.setDate(QDate.currentDate())

        form = QFormLayout()
        form.addRow("Fecha de pago", self.fecha_pago)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def datos(self) -> dict:
        return {"fecha_pago": self.fecha_pago.date().toPython()}


class PagoView(QWidget):
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
        btn_pagado = QPushButton("Marcar pagado")
        btn_documentos = QPushButton("Documentos...")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_pagado.clicked.connect(self._marcar_pagado)
        btn_documentos.clicked.connect(self._documentos)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_editar)
        botones.addWidget(btn_pagado)
        botones.addWidget(btn_documentos)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        pagos = PagoService.listar_por_apartamento(self.apartamento_id)
        self.tabla.setRowCount(0)
        for pago in pagos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(pago.id),
                pago.tipo_servicio.value,
                pago.periodo,
                f"{pago.monto:.2f}",
                pago.proveedor.nombre,
                pago.fecha_vencimiento.isoformat(),
                pago.fecha_pago.isoformat() if pago.fecha_pago else "",
                pago.estado.value,
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
        dialog = PagoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            PagoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        pago_id = self._selected_id()
        if pago_id is None:
            QMessageBox.information(self, "Editar pago", "Selecciona un pago de la tabla.")
            return
        pago = PagoService.obtener(pago_id)
        if pago is None:
            QMessageBox.warning(self, "Error", "El pago ya no existe.")
            self.refrescar()
            return
        dialog = PagoFormDialog(self, pago)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            PagoService.actualizar(pago_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _marcar_pagado(self) -> None:
        pago_id = self._selected_id()
        if pago_id is None:
            QMessageBox.information(self, "Marcar pagado", "Selecciona un pago de la tabla.")
            return
        dialog = MarcarPagadoDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        PagoService.marcar_pagado(pago_id, **dialog.datos())
        self.refrescar()

    def _eliminar(self) -> None:
        pago_id = self._selected_id()
        if pago_id is None:
            QMessageBox.information(self, "Eliminar pago", "Selecciona un pago de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar pago", f"¿Eliminar el pago #{pago_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        PagoService.eliminar(pago_id)
        self.refrescar()

    def _documentos(self) -> None:
        pago_id = self._selected_id()
        if pago_id is None:
            QMessageBox.information(self, "Documentos", "Selecciona un pago de la tabla.")
            return
        pago = PagoService.obtener(pago_id)
        if pago is None:
            QMessageBox.warning(self, "Error", "El pago ya no existe.")
            self.refrescar()
            return
        etiqueta = f"{pago.tipo_servicio.value} ({pago.periodo})"
        DocumentosDeEntidadDialog(EntidadTipo.PAGO_SERVICIO, pago_id, etiqueta, self).exec()
