from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TipoServicio(str, enum.Enum):
    LUZ = "luz"
    AGUA = "agua"
    CABLE_INTERNET = "cable_internet"
    OTRO = "otro"


class EstadoPago(str, enum.Enum):
    PENDIENTE = "pendiente"
    PAGADO = "pagado"
    VENCIDO = "vencido"


class PagoServicio(Base):
    __tablename__ = "pagos_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos.id"), nullable=False)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    tipo_servicio: Mapped[TipoServicio] = mapped_column(
        SqlEnum(TipoServicio, native_enum=False), nullable=False
    )
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoPago] = mapped_column(
        SqlEnum(EstadoPago, native_enum=False),
        default=EstadoPago.PENDIENTE,
        nullable=False,
    )

    apartamento: Mapped[Apartamento] = relationship(back_populates="pagos_servicio")
    proveedor: Mapped[Proveedor] = relationship(back_populates="pagos_servicio")
