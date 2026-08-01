from __future__ import annotations

from sqlalchemy import select

from app.models import Marcador
from app.repositories.base import BaseRepository


class MarcadorRepository(BaseRepository[Marcador]):
    model = Marcador

    def list_by_modelo(self, modelo_3d_id: int) -> list[Marcador]:
        stmt = select(Marcador).where(Marcador.modelo_3d_id == modelo_3d_id)
        return list(self.session.scalars(stmt))
