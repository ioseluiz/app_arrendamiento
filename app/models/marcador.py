from __future__ import annotations

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.documento import EntidadTipo


class Marcador(Base):
    __tablename__ = "marcadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modelo_3d_id: Mapped[int] = mapped_column(ForeignKey("modelos_3d.id"), nullable=False)
    tipo_referencia: Mapped[EntidadTipo | None] = mapped_column(
        SqlEnum(EntidadTipo, native_enum=False), nullable=True
    )
    referencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pos_x: Mapped[float] = mapped_column(Float, nullable=False)
    pos_y: Mapped[float] = mapped_column(Float, nullable=False)
    pos_z: Mapped[float] = mapped_column(Float, nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(255), nullable=False)

    modelo_3d: Mapped[Modelo3D] = relationship(back_populates="marcadores")
