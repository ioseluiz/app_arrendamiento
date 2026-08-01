from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
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

from app.models import Equipo, EstadoEquipo
from app.services import EquipoService

COLUMNS = ["ID", "Nombre", "Tipo", "Ubicación", "Fecha instalación", "Estado"]


class EquipoFormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, equipo: Equipo | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo equipo" if equipo is None else f"Editar equipo #{equipo.id}")

        self.nombre = QLineEdit()
        self.tipo = QLineEdit()
        self.ubicacion = QLineEdit()

        self.fecha_instalacion = QDateEdit(calendarPopup=True)
        self.fecha_instalacion.setDate(QDate.currentDate())
        self.sin_fecha_instalacion = QCheckBox("Sin definir")
        self.sin_fecha_instalacion.toggled.connect(self.fecha_instalacion.setDisabled)
        fila_fecha = QHBoxLayout()
        fila_fecha.addWidget(self.fecha_instalacion)
        fila_fecha.addWidget(self.sin_fecha_instalacion)

        self.estado = QComboBox()
        for estado in EstadoEquipo:
            self.estado.addItem(estado.value, estado)

        if equipo is not None:
            self.nombre.setText(equipo.nombre)
            self.tipo.setText(equipo.tipo)
            self.ubicacion.setText(equipo.ubicacion or "")
            if equipo.fecha_instalacion is not None:
                fecha = equipo.fecha_instalacion
                self.fecha_instalacion.setDate(QDate(fecha.year, fecha.month, fecha.day))
            else:
                self.sin_fecha_instalacion.setChecked(True)
            self.estado.setCurrentIndex(self.estado.findData(equipo.estado))
        else:
            self.sin_fecha_instalacion.setChecked(True)

        form = QFormLayout()
        form.addRow("Nombre", self.nombre)
        form.addRow("Tipo", self.tipo)
        form.addRow("Ubicación", self.ubicacion)
        form.addRow("Fecha instalación", fila_fecha)
        form.addRow("Estado", self.estado)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if not self.nombre.text().strip() or not self.tipo.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "Nombre y tipo son obligatorios.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "nombre": self.nombre.text().strip(),
            "tipo": self.tipo.text().strip(),
            "ubicacion": self.ubicacion.text().strip() or None,
            "fecha_instalacion": (
                None if self.sin_fecha_instalacion.isChecked() else self.fecha_instalacion.date().toPython()
            ),
            "estado": self.estado.currentData(),
        }


class EquipoView(QWidget):
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
        equipos = EquipoService.listar_por_apartamento(self.apartamento_id)
        self.tabla.setRowCount(0)
        for equipo in equipos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(equipo.id),
                equipo.nombre,
                equipo.tipo,
                equipo.ubicacion or "",
                equipo.fecha_instalacion.isoformat() if equipo.fecha_instalacion else "",
                equipo.estado.value,
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
        dialog = EquipoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            EquipoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        equipo_id = self._selected_id()
        if equipo_id is None:
            QMessageBox.information(self, "Editar equipo", "Selecciona un equipo de la tabla.")
            return
        equipo = EquipoService.obtener(equipo_id)
        if equipo is None:
            QMessageBox.warning(self, "Error", "El equipo ya no existe.")
            self.refrescar()
            return
        dialog = EquipoFormDialog(self, equipo)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            EquipoService.actualizar(equipo_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _eliminar(self) -> None:
        equipo_id = self._selected_id()
        if equipo_id is None:
            QMessageBox.information(self, "Eliminar equipo", "Selecciona un equipo de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar equipo", f"¿Eliminar el equipo #{equipo_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        EquipoService.eliminar(equipo_id)
        self.refrescar()
