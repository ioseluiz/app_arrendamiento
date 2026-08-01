from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Modelo3D(Base):
    __tablename__ = "modelos_3d"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(
        ForeignKey("apartamentos.id"), unique=True, nullable=False
    )
    archivo_modelo: Mapped[str] = mapped_column(String(500), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    fecha_actualizacion: Mapped[date] = mapped_column(Date, nullable=False)

    apartamento: Mapped[Apartamento] = relationship(back_populates="modelo_3d")
    marcadores: Mapped[list[Marcador]] = relationship(
        back_populates="modelo_3d", cascade="all, delete-orphan"
    )
