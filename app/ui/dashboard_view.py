from __future__ import annotations

from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QPieSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.services import ReporteService

MESES_HISTORIAL = 6


class StatCard(QFrame):
    def __init__(self, titulo: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #cfcfcf; border-radius: 6px; }"
        )

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet("color: #555555; font-size: 11px; border: none;")
        self.lbl_titulo.setWordWrap(True)

        self.lbl_valor = QLabel("--")
        self.lbl_valor.setStyleSheet("font-size: 22px; font-weight: bold; border: none;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_titulo)
        layout.addWidget(self.lbl_valor)
        layout.addStretch()

    def set_valor(self, texto: str) -> None:
        self.lbl_valor.setText(texto)


class DashboardView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.card_total = StatCard("Gasto histórico total")
        self.card_mes = StatCard("Gasto este mes")
        self.card_pendientes = StatCard("Mantenimientos pendientes")
        self.card_pagos = StatCard("Pagos por vencer (15 días)")
        self.card_recordatorios = StatCard("Recordatorios de mantenimiento")

        tarjetas = QHBoxLayout()
        for card in (
            self.card_total,
            self.card_mes,
            self.card_pendientes,
            self.card_pagos,
            self.card_recordatorios,
        ):
            tarjetas.addWidget(card)

        self.chart_view_mensual = QChartView()
        self.chart_view_mensual.setRenderHint(QPainter.Antialiasing)
        self.chart_view_mensual.setMinimumHeight(280)

        self.chart_view_categorias = QChartView()
        self.chart_view_categorias.setRenderHint(QPainter.Antialiasing)
        self.chart_view_categorias.setMinimumHeight(280)

        graficos = QHBoxLayout()
        graficos.addWidget(self.chart_view_mensual, 2)
        graficos.addWidget(self.chart_view_categorias, 1)

        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.clicked.connect(self.refrescar)

        cabecera = QHBoxLayout()
        cabecera.addWidget(QLabel("<h2>Dashboard</h2>"))
        cabecera.addStretch()
        cabecera.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(cabecera)
        layout.addLayout(tarjetas)
        layout.addLayout(graficos, 1)

        self.refrescar()

    def refrescar(self) -> None:
        resumen = ReporteService.resumen_dashboard(self.apartamento_id)
        self.card_total.set_valor(f"{resumen.total_historico:,.2f}")
        self.card_mes.set_valor(f"{resumen.gasto_mes_actual:,.2f}")
        self.card_pendientes.set_valor(str(resumen.mantenimientos_pendientes))
        self.card_pagos.set_valor(str(resumen.pagos_por_vencer))
        self.card_recordatorios.set_valor(str(resumen.recordatorios_mantenimiento))

        self._actualizar_grafico_mensual()
        self._actualizar_grafico_categorias()

    def _actualizar_grafico_mensual(self) -> None:
        serie_datos = ReporteService.gastos_por_mes(self.apartamento_id, meses=MESES_HISTORIAL)

        barset = QBarSet("Gastos")
        for _, monto in serie_datos:
            barset.append(monto)

        series = QBarSeries()
        series.append(barset)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Gastos mensuales (últimos {MESES_HISTORIAL} meses)")
        chart.legend().setVisible(False)

        eje_x = QBarCategoryAxis()
        eje_x.append([etiqueta for etiqueta, _ in serie_datos])
        chart.addAxis(eje_x, Qt.AlignBottom)
        series.attachAxis(eje_x)

        maximo = max((monto for _, monto in serie_datos), default=0)
        eje_y = QValueAxis()
        eje_y.setRange(0, maximo * 1.2 if maximo > 0 else 10)
        chart.addAxis(eje_y, Qt.AlignLeft)
        series.attachAxis(eje_y)

        self.chart_view_mensual.setChart(chart)

    def _actualizar_grafico_categorias(self) -> None:
        datos = [(categoria, monto) for categoria, monto in ReporteService.gastos_por_categoria(self.apartamento_id) if monto > 0]

        chart = QChart()
        chart.setTitle("Gastos por categoría" if datos else "Gastos por categoría (sin datos)")

        if datos:
            series = QPieSeries()
            for categoria, monto in datos:
                series.append(f"{categoria} ({monto:,.0f})", monto)
            chart.addSeries(series)

        self.chart_view_categorias.setChart(chart)
