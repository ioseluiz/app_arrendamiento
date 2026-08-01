from __future__ import annotations

from sqlalchemy import select

from app.models import Contrato
from app.repositories.base import BaseRepository


class ContratoRepository(BaseRepository[Contrato]):
    model = Contrato

    def list_by_apartamento(self, apartamento_id: int) -> list[Contrato]:
        stmt = select(Contrato).where(Contrato.apartamento_id == apartamento_id)
        return list(self.session.scalars(stmt))
