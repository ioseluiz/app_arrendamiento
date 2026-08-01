from app.models.apartamento import Apartamento
from app.models.base import Base, SessionLocal, engine
from app.models.contrato import Contrato, EstadoContrato
from app.models.documento import Documento, EntidadTipo, TipoDocumento
from app.models.equipo import Equipo, EstadoEquipo
from app.models.mantenimiento import EstadoMantenimiento, Mantenimiento
from app.models.pago_servicio import EstadoPago, PagoServicio, TipoServicio
from app.models.proveedor import Proveedor

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "init_db",
    "Apartamento",
    "Contrato",
    "EstadoContrato",
    "Documento",
    "EntidadTipo",
    "TipoDocumento",
    "Equipo",
    "EstadoEquipo",
    "Mantenimiento",
    "EstadoMantenimiento",
    "PagoServicio",
    "TipoServicio",
    "EstadoPago",
    "Proveedor",
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
