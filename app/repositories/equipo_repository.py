from __future__ import annotations

from sqlalchemy import select

from app.models import Equipo
from app.repositories.base import BaseRepository


class EquipoRepository(BaseRepository[Equipo]):
    model = Equipo

    def list_by_apartamento(self, apartamento_id: int) -> list[Equipo]:
        stmt = select(Equipo).where(Equipo.apartamento_id == apartamento_id)
        return list(self.session.scalars(stmt))
