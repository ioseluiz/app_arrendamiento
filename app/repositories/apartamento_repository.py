from __future__ import annotations

from app.models import Apartamento
from app.repositories.base import BaseRepository


class ApartamentoRepository(BaseRepository[Apartamento]):
    model = Apartamento
