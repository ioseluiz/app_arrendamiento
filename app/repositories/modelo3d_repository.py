from __future__ import annotations

from sqlalchemy import select

from app.models import Modelo3D
from app.repositories.base import BaseRepository


class Modelo3DRepository(BaseRepository[Modelo3D]):
    model = Modelo3D

    def get_by_apartamento(self, apartamento_id: int) -> Modelo3D | None:
        stmt = select(Modelo3D).where(Modelo3D.apartamento_id == apartamento_id)
        return self.session.scalars(stmt).first()
