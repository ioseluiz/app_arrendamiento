from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.models import EstadoMantenimiento, EstadoPago, Mantenimiento, PagoServicio
from app.services.mantenimiento_service import MantenimientoService
from app.services.pago_servicio_service import PagoService


@dataclass(frozen=True)
class GastoItem:
    fecha: date
    concepto: str
    categoria: str
    monto: float


class ReporteService:
    @staticmethod
    def historial_gastos(apartamento_id: int) -> list[GastoItem]:
        gastos: list[GastoItem] = []
        for mant in MantenimientoService.listar_por_apartamento(apartamento_id):
            if mant.estado == EstadoMantenimiento.COMPLETADO and mant.costo is not None:
                gastos.append(
                    GastoItem(
                        fecha=mant.fecha_completado or mant.fecha_solicitud,
                        concepto=mant.titulo,
                        categoria="Mantenimiento",
                        monto=mant.costo,
                    )
                )
        for pago in PagoService.listar_por_apartamento(apartamento_id):
            if pago.estado == EstadoPago.PAGADO:
                gastos.append(
                    GastoItem(
                        fecha=pago.fecha_pago or pago.fecha_vencimiento,
                        concepto=f"{pago.tipo_servicio.value} ({pago.periodo})",
                        categoria="Pago de servicio",
                        monto=pago.monto,
                    )
                )
        gastos.sort(key=lambda g: g.fecha, reverse=True)
        return gastos

    @staticmethod
    def mantenimiento_pendiente(apartamento_id: int) -> list[Mantenimiento]:
        pendientes = [
            m
            for m in MantenimientoService.listar_por_apartamento(apartamento_id)
            if m.estado != EstadoMantenimiento.COMPLETADO
        ]
        pendientes.sort(key=lambda m: m.fecha_solicitud)
        return pendientes

    @staticmethod
    def pagos_proximos_a_vencer(apartamento_id: int, dias: int = 15) -> list[PagoServicio]:
        limite = date.today() + timedelta(days=dias)
        proximos = [
            p
            for p in PagoService.listar_por_apartamento(apartamento_id)
            if p.estado != EstadoPago.PAGADO and p.fecha_vencimiento <= limite
        ]
        proximos.sort(key=lambda p: p.fecha_vencimiento)
        return proximos
