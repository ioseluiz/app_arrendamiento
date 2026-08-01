from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
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
from sqlalchemy.exc import IntegrityError

from app.models import Proveedor
from app.services import ProveedorService

COLUMNS = ["ID", "Nombre", "Tipo de servicio", "Teléfono", "Email"]


class ProveedorFormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, proveedor: Proveedor | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo proveedor" if proveedor is None else f"Editar proveedor #{proveedor.id}")

        self.nombre = QLineEdit()
        self.tipo_servicio = QLineEdit()
        self.telefono = QLineEdit()
        self.email = QLineEdit()

        if proveedor is not None:
            self.nombre.setText(proveedor.nombre)
            self.tipo_servicio.setText(proveedor.tipo_servicio)
            self.telefono.setText(proveedor.telefono or "")
            self.email.setText(proveedor.email or "")

        form = QFormLayout()
        form.addRow("Nombre", self.nombre)
        form.addRow("Tipo de servicio", self.tipo_servicio)
        form.addRow("Teléfono", self.telefono)
        form.addRow("Email", self.email)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if not self.nombre.text().strip() or not self.tipo_servicio.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "Nombre y tipo de servicio son obligatorios.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "nombre": self.nombre.text().strip(),
            "tipo_servicio": self.tipo_servicio.text().strip(),
            "telefono": self.telefono.text().strip() or None,
            "email": self.email.text().strip() or None,
        }


class ProveedorView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.tabla = QTableWidget(0, len(COLUMNS))
        self.tabla.setHorizontalHeaderLabels(COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_nuevo = QPushButton("Nuevo")
        btn_editar = QPushButton("Editar")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_editar)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        proveedores = ProveedorService.listar()
        self.tabla.setRowCount(0)
        for proveedor in proveedores:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(proveedor.id),
                proveedor.nombre,
                proveedor.tipo_servicio,
                proveedor.telefono or "",
                proveedor.email or "",
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
        dialog = ProveedorFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            ProveedorService.crear(**dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        proveedor_id = self._selected_id()
        if proveedor_id is None:
            QMessageBox.information(self, "Editar proveedor", "Selecciona un proveedor de la tabla.")
            return
        proveedor = ProveedorService.obtener(proveedor_id)
        if proveedor is None:
            QMessageBox.warning(self, "Error", "El proveedor ya no existe.")
            self.refrescar()
            return
        dialog = ProveedorFormDialog(self, proveedor)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            ProveedorService.actualizar(proveedor_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _eliminar(self) -> None:
        proveedor_id = self._selected_id()
        if proveedor_id is None:
            QMessageBox.information(self, "Eliminar proveedor", "Selecciona un proveedor de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar proveedor", f"¿Eliminar el proveedor #{proveedor_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            ProveedorService.eliminar(proveedor_id)
        except IntegrityError:
            QMessageBox.warning(
                self,
                "No se pudo eliminar",
                "El proveedor tiene mantenimientos o pagos asociados y no puede eliminarse.",
            )
            return
        self.refrescar()
