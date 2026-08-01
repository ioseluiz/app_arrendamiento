from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services import ReporteService

GASTOS_COLUMNS = ["Fecha", "Concepto", "Categoría", "Monto"]
PENDIENTES_COLUMNS = ["Título", "Estado", "Fecha solicitud", "Equipo"]
VENCIMIENTOS_COLUMNS = ["Servicio", "Periodo", "Monto", "Vencimiento", "Situación"]

DIAS_ALERTA_VENCIMIENTO = 15


def _tabla_solo_lectura(columnas: list[str]) -> QTableWidget:
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.horizontalHeader().setStretchLastSection(True)
    tabla.setMaximumHeight(180)
    return tabla


class ReporteView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.lbl_total_gastos = QLabel()
        self.tabla_gastos = _tabla_solo_lectura(GASTOS_COLUMNS)
        self.tabla_pendientes = _tabla_solo_lectura(PENDIENTES_COLUMNS)
        self.tabla_vencimientos = _tabla_solo_lectura(VENCIMIENTOS_COLUMNS)

        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.clicked.connect(self.refrescar)

        cabecera = QHBoxLayout()
        cabecera.addWidget(QLabel("<h3>Reportes</h3>"))
        cabecera.addStretch()
        cabecera.addWidget(btn_refrescar)

        fila_gastos = QHBoxLayout()
        fila_gastos.addWidget(QLabel("<b>Historial de gastos</b>"))
        fila_gastos.addStretch()
        fila_gastos.addWidget(self.lbl_total_gastos)

        layout = QVBoxLayout(self)
        layout.addLayout(cabecera)
        layout.addLayout(fila_gastos)
        layout.addWidget(self.tabla_gastos)
        layout.addWidget(QLabel("<b>Mantenimiento pendiente</b>"))
        layout.addWidget(self.tabla_pendientes)
        layout.addWidget(
            QLabel(f"<b>Pagos vencidos o próximos a vencer ({DIAS_ALERTA_VENCIMIENTO} días)</b>")
        )
        layout.addWidget(self.tabla_vencimientos)

        self.refrescar()

    def refrescar(self) -> None:
        self._refrescar_gastos()
        self._refrescar_pendientes()
        self._refrescar_vencimientos()

    def _refrescar_gastos(self) -> None:
        gastos = ReporteService.historial_gastos(self.apartamento_id)
        self.tabla_gastos.setRowCount(0)
        total = 0.0
        for gasto in gastos:
            row = self.tabla_gastos.rowCount()
            self.tabla_gastos.insertRow(row)
            valores = [gasto.fecha.isoformat(), gasto.concepto, gasto.categoria, f"{gasto.monto:.2f}"]
            for col, valor in enumerate(valores):
                self.tabla_gastos.setItem(row, col, QTableWidgetItem(valor))
            total += gasto.monto
        self.lbl_total_gastos.setText(f"Total: {total:.2f}")

    def _refrescar_pendientes(self) -> None:
        pendientes = ReporteService.mantenimiento_pendiente(self.apartamento_id)
        self.tabla_pendientes.setRowCount(0)
        for mant in pendientes:
            row = self.tabla_pendientes.rowCount()
            self.tabla_pendientes.insertRow(row)
            valores = [
                mant.titulo,
                mant.estado.value,
                mant.fecha_solicitud.isoformat(),
                mant.equipo.nombre if mant.equipo_id else "",
            ]
            for col, valor in enumerate(valores):
                self.tabla_pendientes.setItem(row, col, QTableWidgetItem(valor))

    def _refrescar_vencimientos(self) -> None:
        pagos = ReporteService.pagos_proximos_a_vencer(self.apartamento_id, dias=DIAS_ALERTA_VENCIMIENTO)
        self.tabla_vencimientos.setRowCount(0)
        hoy = date.today()
        for pago in pagos:
            row = self.tabla_vencimientos.rowCount()
            self.tabla_vencimientos.insertRow(row)
            situacion = "Vencido" if pago.fecha_vencimiento < hoy else "Próximo"
            valores = [
                pago.tipo_servicio.value,
                pago.periodo,
                f"{pago.monto:.2f}",
                pago.fecha_vencimiento.isoformat(),
                situacion,
            ]
            for col, valor in enumerate(valores):
                self.tabla_vencimientos.setItem(row, col, QTableWidgetItem(valor))
