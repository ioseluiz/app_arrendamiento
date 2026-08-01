from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.services import ApartamentoService
from app.ui.apartamento_view import ApartamentoView
from app.ui.contrato_view import ContratoView
from app.ui.documento_view import DocumentoView
from app.ui.equipo_view import EquipoView
from app.ui.mantenimiento_view import MantenimientoView
from app.ui.pago_servicio_view import PagoView
from app.ui.proveedor_view import ProveedorView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arrendamiento")
        self.resize(1000, 650)

        apartamento_id = self._apartamento_principal_id()

        tabs = QTabWidget()
        tabs.addTab(ApartamentoView(apartamento_id), "Apartamento")
        tabs.addTab(ContratoView(apartamento_id), "Contrato")
        tabs.addTab(EquipoView(apartamento_id), "Equipos")
        tabs.addTab(ProveedorView(), "Proveedores")
        tabs.addTab(MantenimientoView(apartamento_id), "Mantenimiento")
        tabs.addTab(PagoView(apartamento_id), "Pagos")
        tabs.addTab(DocumentoView(), "Documentos")
        self.setCentralWidget(tabs)

    @staticmethod
    def _apartamento_principal_id() -> int:
        apartamentos = ApartamentoService.listar()
        if apartamentos:
            return apartamentos[0].id
        apartamento = ApartamentoService.crear(direccion="Mi apartamento (editar dirección)")
        return apartamento.id
