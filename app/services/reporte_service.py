from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.date_utils import sumar_meses
from app.models import EstadoMantenimiento, EstadoPago, Mantenimiento, PagoServicio, TipoServicio
from app.services.mantenimiento_service import MantenimientoService
from app.services.pago_servicio_service import PagoService
from app.services.recordatorio_service import RecordatorioService

MESES_ABREV = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _categoria_de_tipo_servicio(tipo: TipoServicio) -> str:
    return tipo.value.replace("_", "/").title()


def _categoria_pago(pago: PagoServicio) -> str:
    return _categoria_de_tipo_servicio(pago.tipo_servicio)


@dataclass(frozen=True)
class GastoItem:
    fecha: date
    concepto: str
    categoria: str
    monto: float


@dataclass(frozen=True)
class ResumenDashboard:
    total_historico: float
    gasto_mes_actual: float
    mantenimientos_pendientes: int
    pagos_por_vencer: int
    recordatorios_mantenimiento: int


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
                        categoria=_categoria_pago(pago),
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
    def historial_mantenimientos(apartamento_id: int) -> list[Mantenimiento]:
        completados = [
            m
            for m in MantenimientoService.listar_por_apartamento(apartamento_id)
            if m.estado == EstadoMantenimiento.COMPLETADO
        ]
        completados.sort(key=lambda m: m.fecha_completado or m.fecha_solicitud, reverse=True)
        return completados

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

    @staticmethod
    def gastos_por_mes(
        apartamento_id: int, meses: int = 6, categoria: str | None = None
    ) -> list[tuple[str, float]]:
        hoy = date.today()
        primer_mes = sumar_meses(date(hoy.year, hoy.month, 1), -(meses - 1))
        claves: list[tuple[int, int]] = []
        cursor = primer_mes
        for _ in range(meses):
            claves.append((cursor.year, cursor.month))
            cursor = sumar_meses(cursor, 1)

        totales = {clave: 0.0 for clave in claves}
        for gasto in ReporteService.historial_gastos(apartamento_id):
            if categoria is not None and gasto.categoria != categoria:
                continue
            clave = (gasto.fecha.year, gasto.fecha.month)
            if clave in totales:
                totales[clave] += gasto.monto

        return [(f"{MESES_ABREV[mes - 1]} {anio}", totales[(anio, mes)]) for anio, mes in claves]

    @staticmethod
    def gastos_por_categoria(apartamento_id: int) -> list[tuple[str, float]]:
        totales: dict[str, float] = {}
        for gasto in ReporteService.historial_gastos(apartamento_id):
            totales[gasto.categoria] = totales.get(gasto.categoria, 0.0) + gasto.monto
        return sorted(totales.items(), key=lambda item: item[1], reverse=True)

    @staticmethod
    def categorias_disponibles() -> list[str]:
        """Todas las categorías de gasto posibles (coincide con las que
        genera historial_gastos), para poblar un filtro sin depender de que
        ya haya datos cargados en cada una."""
        return ["Mantenimiento"] + [_categoria_de_tipo_servicio(t) for t in TipoServicio]

    @staticmethod
    def resumen_dashboard(apartamento_id: int) -> ResumenDashboard:
        hoy = date.today()
        gastos = ReporteService.historial_gastos(apartamento_id)
        return ResumenDashboard(
            total_historico=sum(g.monto for g in gastos),
            gasto_mes_actual=sum(
                g.monto for g in gastos if g.fecha.year == hoy.year and g.fecha.month == hoy.month
            ),
            mantenimientos_pendientes=len(ReporteService.mantenimiento_pendiente(apartamento_id)),
            pagos_por_vencer=len(ReporteService.pagos_proximos_a_vencer(apartamento_id)),
            recordatorios_mantenimiento=len(RecordatorioService.proximos_mantenimientos(apartamento_id)),
        )
