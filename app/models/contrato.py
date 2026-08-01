from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EstadoContrato(str, enum.Enum):
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    RENOVADO = "renovado"


class Contrato(Base):
    __tablename__ = "contratos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos.id"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    monto_mensual: Mapped[float] = mapped_column(Float, nullable=False)
    arrendador: Mapped[str] = mapped_column(String(255), nullable=False)
    arrendatario: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoContrato] = mapped_column(
        SqlEnum(EstadoContrato, native_enum=False),
        default=EstadoContrato.ACTIVO,
        nullable=False,
    )

    apartamento: Mapped[Apartamento] = relationship(back_populates="contratos")
