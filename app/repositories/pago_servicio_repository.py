from __future__ import annotations

from sqlalchemy import select

from app.models import PagoServicio
from app.repositories.base import BaseRepository


class PagoServicioRepository(BaseRepository[PagoServicio]):
    model = PagoServicio

    def list_by_apartamento(self, apartamento_id: int) -> list[PagoServicio]:
        stmt = select(PagoServicio).where(PagoServicio.apartamento_id == apartamento_id)
        return list(self.session.scalars(stmt))
