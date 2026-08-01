from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.services import ApartamentoService
from app.ui.apartamento_view import ApartamentoView
from app.ui.contrato_view import ContratoView
from app.ui.dashboard_view import DashboardView
from app.ui.documento_view import DocumentoView
from app.ui.equipo_view import EquipoView
from app.ui.mantenimiento_view import MantenimientoView
from app.ui.pago_servicio_view import PagoView
from app.ui.proveedor_view import ProveedorView
from app.ui.reporte_view import ReporteView
from app.ui.viewer3d_view import Viewer3DView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arrendamiento")
        self.resize(1100, 700)

        apartamento_id = self._apartamento_principal_id()

        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardView(apartamento_id), "Dashboard")
        self.tabs.addTab(ApartamentoView(apartamento_id), "Apartamento")
        self.tabs.addTab(ContratoView(apartamento_id), "Contrato")
        self.tabs.addTab(EquipoView(apartamento_id), "Equipos")
        self.tabs.addTab(ProveedorView(), "Proveedores")
        self.tabs.addTab(MantenimientoView(apartamento_id), "Mantenimiento")
        self.tabs.addTab(PagoView(apartamento_id), "Pagos")
        self.tabs.addTab(ReporteView(apartamento_id), "Reportes")
        self.tabs.addTab(DocumentoView(apartamento_id), "Documentos")
        self.tabs.addTab(Viewer3DView(apartamento_id), "Modelo 3D")
        self.tabs.currentChanged.connect(self._al_cambiar_pestana)
        self.setCentralWidget(self.tabs)

    def _al_cambiar_pestana(self, index: int) -> None:
        widget = self.tabs.widget(index)
        refrescar = getattr(widget, "refrescar", None)
        if callable(refrescar):
            refrescar()

    @staticmethod
    def _apartamento_principal_id() -> int:
        apartamentos = ApartamentoService.listar()
        if apartamentos:
            return apartamentos[0].id
        apartamento = ApartamentoService.crear(direccion="Mi apartamento (editar dirección)")
        return apartamento.id
