from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TipoDocumento(str, enum.Enum):
    PDF = "pdf"
    FOTO = "foto"
    OTRO = "otro"


class EntidadTipo(str, enum.Enum):
    """A qué tipo de entidad está asociado el documento (asociación polimórfica)."""

    CONTRATO = "contrato"
    EQUIPO = "equipo"
    MANTENIMIENTO = "mantenimiento"
    PAGO_SERVICIO = "pago_servicio"


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[TipoDocumento] = mapped_column(SqlEnum(TipoDocumento, native_enum=False), nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    fecha_subida: Mapped[date] = mapped_column(Date, nullable=False)
    entidad_tipo: Mapped[EntidadTipo] = mapped_column(
        SqlEnum(EntidadTipo, native_enum=False), nullable=False
    )
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False)
