from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EstadoMantenimiento(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"


class Mantenimiento(Base):
    __tablename__ = "mantenimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos.id"), nullable=False)
    equipo_id: Mapped[int | None] = mapped_column(ForeignKey("equipos.id"), nullable=True)
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[EstadoMantenimiento] = mapped_column(
        SqlEnum(EstadoMantenimiento, native_enum=False),
        default=EstadoMantenimiento.PENDIENTE,
        nullable=False,
    )
    fecha_solicitud: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_completado: Mapped[date | None] = mapped_column(Date, nullable=True)
    costo: Mapped[float | None] = mapped_column(Float, nullable=True)

    apartamento: Mapped[Apartamento] = relationship(back_populates="mantenimientos")
    equipo: Mapped[Equipo | None] = relationship(back_populates="mantenimientos")
    proveedor: Mapped[Proveedor | None] = relationship(back_populates="mantenimientos")
