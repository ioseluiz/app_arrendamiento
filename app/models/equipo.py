from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EstadoEquipo(str, enum.Enum):
    OPERATIVO = "operativo"
    EN_REPARACION = "en_reparacion"
    FUERA_DE_SERVICIO = "fuera_de_servicio"


class Equipo(Base):
    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha_instalacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoEquipo] = mapped_column(
        SqlEnum(EstadoEquipo, native_enum=False),
        default=EstadoEquipo.OPERATIVO,
        nullable=False,
    )
    frecuencia_mantenimiento_meses: Mapped[int | None] = mapped_column(Integer, nullable=True)

    apartamento: Mapped[Apartamento] = relationship(back_populates="equipos")
    mantenimientos: Mapped[list[Mantenimiento]] = relationship(back_populates="equipo")
