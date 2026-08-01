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
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models import EstadoMantenimiento, Mantenimiento
from app.services import EquipoService, MantenimientoService, ProveedorService

COLUMNS = ["ID", "Título", "Equipo", "Proveedor", "Estado", "Solicitud", "Completado", "Costo"]


class MantenimientoFormDialog(QDialog):
    def __init__(
        self,
        apartamento_id: int,
        parent: QWidget | None = None,
        mantenimiento: Mantenimiento | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(
            "Nuevo mantenimiento" if mantenimiento is None else f"Editar mantenimiento #{mantenimiento.id}"
        )

        self.titulo = QLineEdit()
        self.descripcion = QPlainTextEdit()
        self.descripcion.setFixedHeight(80)

        self.equipo = QComboBox()
        self.equipo.addItem("(ninguno)", None)
        for equipo in EquipoService.listar_por_apartamento(apartamento_id):
            self.equipo.addItem(equipo.nombre, equipo.id)

        self.proveedor = QComboBox()
        self.proveedor.addItem("(sin asignar)", None)
        for proveedor in ProveedorService.listar():
            self.proveedor.addItem(proveedor.nombre, proveedor.id)

        self.estado = QComboBox()
        for estado in EstadoMantenimiento:
            self.estado.addItem(estado.value, estado)

        self.fecha_solicitud = QDateEdit(calendarPopup=True)
        self.fecha_solicitud.setDate(QDate.currentDate())

        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 1_000_000)
        self.costo.setDecimals(2)
        self.costo.setSpecialValueText("(sin especificar)")

        if mantenimiento is not None:
            self.titulo.setText(mantenimiento.titulo)
            self.descripcion.setPlainText(mantenimiento.descripcion or "")
            self.equipo.setCurrentIndex(self.equipo.findData(mantenimiento.equipo_id))
            self.proveedor.setCurrentIndex(self.proveedor.findData(mantenimiento.proveedor_id))
            self.estado.setCurrentIndex(self.estado.findData(mantenimiento.estado))
            fs = mantenimiento.fecha_solicitud
            self.fecha_solicitud.setDate(QDate(fs.year, fs.month, fs.day))
            self.costo.setValue(mantenimiento.costo or 0)

        form = QFormLayout()
        form.addRow("Título", self.titulo)
        form.addRow("Descripción", self.descripcion)
        form.addRow("Equipo", self.equipo)
        form.addRow("Proveedor", self.proveedor)
        form.addRow("Estado", self.estado)
        form.addRow("Fecha de solicitud", self.fecha_solicitud)
        form.addRow("Costo", self.costo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if not self.titulo.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El título es obligatorio.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "titulo": self.titulo.text().strip(),
            "descripcion": self.descripcion.toPlainText().strip() or None,
            "equipo_id": self.equipo.currentData(),
            "proveedor_id": self.proveedor.currentData(),
            "estado": self.estado.currentData(),
            "fecha_solicitud": self.fecha_solicitud.date().toPython(),
            "costo": self.costo.value() or None,
        }


class MarcarCompletadoDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Marcar como completado")

        self.fecha_completado = QDateEdit(calendarPopup=True)
        self.fecha_completado.setDate(QDate.currentDate())

        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 1_000_000)
        self.costo.setDecimals(2)
        self.costo.setSpecialValueText("(sin especificar)")

        form = QFormLayout()
        form.addRow("Fecha de finalización", self.fecha_completado)
        form.addRow("Costo", self.costo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def datos(self) -> dict:
        return {
            "fecha_completado": self.fecha_completado.date().toPython(),
            "costo": self.costo.value() or None,
        }


class MantenimientoView(QWidget):
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
        btn_completado = QPushButton("Marcar completado")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_completado.clicked.connect(self._marcar_completado)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_editar)
        botones.addWidget(btn_completado)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        mantenimientos = MantenimientoService.listar_por_apartamento(self.apartamento_id)
        self.tabla.setRowCount(0)
        for mant in mantenimientos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(mant.id),
                mant.titulo,
                mant.equipo.nombre if mant.equipo_id else "",
                mant.proveedor.nombre if mant.proveedor_id else "",
                mant.estado.value,
                mant.fecha_solicitud.isoformat(),
                mant.fecha_completado.isoformat() if mant.fecha_completado else "",
                f"{mant.costo:.2f}" if mant.costo is not None else "",
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
        dialog = MantenimientoFormDialog(self.apartamento_id, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            MantenimientoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Editar mantenimiento", "Selecciona un mantenimiento de la tabla.")
            return
        mant = MantenimientoService.obtener(mant_id)
        if mant is None:
            QMessageBox.warning(self, "Error", "El mantenimiento ya no existe.")
            self.refrescar()
            return
        dialog = MantenimientoFormDialog(self.apartamento_id, self, mant)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            MantenimientoService.actualizar(mant_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _marcar_completado(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Marcar completado", "Selecciona un mantenimiento de la tabla.")
            return
        dialog = MarcarCompletadoDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        MantenimientoService.marcar_completado(mant_id, **dialog.datos())
        self.refrescar()

    def _eliminar(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Eliminar mantenimiento", "Selecciona un mantenimiento de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar mantenimiento", f"¿Eliminar el mantenimiento #{mant_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        MantenimientoService.eliminar(mant_id)
        self.refrescar()
