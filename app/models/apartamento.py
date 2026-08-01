from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Apartamento(Base):
    __tablename__ = "apartamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    habitaciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    banos: Mapped[int | None] = mapped_column(Integer, nullable=True)

    contratos: Mapped[list["Contrato"]] = relationship(
        back_populates="apartamento", cascade="all, delete-orphan"
    )
    equipos: Mapped[list["Equipo"]] = relationship(
        back_populates="apartamento", cascade="all, delete-orphan"
    )
    mantenimientos: Mapped[list["Mantenimiento"]] = relationship(
        back_populates="apartamento", cascade="all, delete-orphan"
    )
    pagos_servicio: Mapped[list["PagoServicio"]] = relationship(
        back_populates="apartamento", cascade="all, delete-orphan"
    )
    modelo_3d: Mapped["Modelo3D | None"] = relationship(
        back_populates="apartamento", uselist=False, cascade="all, delete-orphan"
    )
