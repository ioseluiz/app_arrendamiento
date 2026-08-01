from __future__ import annotations

from sqlalchemy import select

from app.models import Documento, EntidadTipo
from app.repositories.base import BaseRepository


class DocumentoRepository(BaseRepository[Documento]):
    model = Documento

    def list_by_entidad(self, entidad_tipo: EntidadTipo, entidad_id: int) -> list[Documento]:
        stmt = select(Documento).where(
            Documento.entidad_tipo == entidad_tipo, Documento.entidad_id == entidad_id
        )
        return list(self.session.scalars(stmt))
