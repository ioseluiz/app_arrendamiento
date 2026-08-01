from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import EstadoMantenimiento, Mantenimiento
from app.repositories.base import BaseRepository


class MantenimientoRepository(BaseRepository[Mantenimiento]):
    model = Mantenimiento

    def list_by_apartamento(self, apartamento_id: int) -> list[Mantenimiento]:
        stmt = (
            select(Mantenimiento)
            .where(Mantenimiento.apartamento_id == apartamento_id)
            .options(selectinload(Mantenimiento.equipo), selectinload(Mantenimiento.proveedor))
        )
        return list(self.session.scalars(stmt))

    def list_by_estado(self, estado: EstadoMantenimiento) -> list[Mantenimiento]:
        stmt = (
            select(Mantenimiento)
            .where(Mantenimiento.estado == estado)
            .options(selectinload(Mantenimiento.equipo), selectinload(Mantenimiento.proveedor))
        )
        return list(self.session.scalars(stmt))
