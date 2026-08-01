from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.date_utils import sumar_meses
from app.models import EstadoMantenimiento
from app.services.equipo_service import EquipoService
from app.services.mantenimiento_service import MantenimientoService


@dataclass(frozen=True)
class RecordatorioMantenimiento:
    equipo_id: int
    equipo_nombre: str
    frecuencia_meses: int
    ultimo_mantenimiento: date | None
    proxima_fecha: date
    dias_restantes: int  # negativo = vencido


class RecordatorioService:
    @staticmethod
    def proximos_mantenimientos(apartamento_id: int, dias: int = 30) -> list[RecordatorioMantenimiento]:
        equipos = EquipoService.listar_por_apartamento(apartamento_id)
        equipos_programados = [e for e in equipos if e.frecuencia_mantenimiento_meses]
        if not equipos_programados:
            return []

        ultimo_por_equipo: dict[int, date] = {}
        for mant in MantenimientoService.listar_por_apartamento(apartamento_id):
            if mant.estado != EstadoMantenimiento.COMPLETADO or mant.equipo_id is None:
                continue
            fecha = mant.fecha_completado
            if fecha is None:
                continue
            actual = ultimo_por_equipo.get(mant.equipo_id)
            if actual is None or fecha > actual:
                ultimo_por_equipo[mant.equipo_id] = fecha

        hoy = date.today()
        recordatorios: list[RecordatorioMantenimiento] = []
        for equipo in equipos_programados:
            base = ultimo_por_equipo.get(equipo.id) or equipo.fecha_instalacion
            if base is None:
                continue
            proxima_fecha = sumar_meses(base, equipo.frecuencia_mantenimiento_meses)
            dias_restantes = (proxima_fecha - hoy).days
            if dias_restantes <= dias:
                recordatorios.append(
                    RecordatorioMantenimiento(
                        equipo_id=equipo.id,
                        equipo_nombre=equipo.nombre,
                        frecuencia_meses=equipo.frecuencia_mantenimiento_meses,
                        ultimo_mantenimiento=ultimo_por_equipo.get(equipo.id),
                        proxima_fecha=proxima_fecha,
                        dias_restantes=dias_restantes,
                    )
                )
        recordatorios.sort(key=lambda r: r.proxima_fecha)
        return recordatorios
