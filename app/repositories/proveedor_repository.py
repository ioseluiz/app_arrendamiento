from __future__ import annotations

from app.models import Proveedor
from app.repositories.base import BaseRepository


class ProveedorRepository(BaseRepository[Proveedor]):
    model = Proveedor
