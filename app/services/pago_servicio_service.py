from __future__ import annotations

from datetime import date

from app.models import EstadoPago, PagoServicio, SessionLocal, TipoServicio
from app.repositories import PagoServicioRepository


class PagoService:
    @staticmethod
    def crear(
        apartamento_id: int,
        proveedor_id: int,
        tipo_servicio: TipoServicio,
        periodo: str,
        monto: float,
        fecha_vencimiento: date,
        estado: EstadoPago = EstadoPago.PENDIENTE,
    ) -> PagoServicio:
        PagoService._validar(monto)
        with SessionLocal() as session:
            repo = PagoServicioRepository(session)
            pago = repo.add(
                PagoServicio(
                    apartamento_id=apartamento_id,
                    proveedor_id=proveedor_id,
                    tipo_servicio=tipo_servicio,
                    periodo=periodo,
                    monto=monto,
                    fecha_vencimiento=fecha_vencimiento,
                    estado=estado,
                )
            )
            session.commit()
            return pago

    @staticmethod
    def obtener(pago_id: int) -> PagoServicio | None:
        with SessionLocal() as session:
            return PagoServicioRepository(session).get(pago_id)

    @staticmethod
    def listar_por_apartamento(apartamento_id: int) -> list[PagoServicio]:
        with SessionLocal() as session:
            return PagoServicioRepository(session).list_by_apartamento(apartamento_id)

    @staticmethod
    def actualizar(pago_id: int, **cambios) -> PagoServicio:
        with SessionLocal() as session:
            repo = PagoServicioRepository(session)
            pago = repo.get(pago_id)
            if pago is None:
                raise ValueError(f"Pago {pago_id} no existe")
            for campo, valor in cambios.items():
                setattr(pago, campo, valor)
            PagoService._validar(pago.monto)
            session.commit()
            return pago

    @staticmethod
    def marcar_pagado(pago_id: int, fecha_pago: date | None = None) -> PagoServicio:
        with SessionLocal() as session:
            repo = PagoServicioRepository(session)
            pago = repo.get(pago_id)
            if pago is None:
                raise ValueError(f"Pago {pago_id} no existe")
            pago.estado = EstadoPago.PAGADO
            pago.fecha_pago = fecha_pago or date.today()
            session.commit()
            return pago

    @staticmethod
    def eliminar(pago_id: int) -> None:
        with SessionLocal() as session:
            repo = PagoServicioRepository(session)
            pago = repo.get(pago_id)
            if pago is None:
                raise ValueError(f"Pago {pago_id} no existe")
            repo.delete(pago)
            session.commit()

    @staticmethod
    def _validar(monto: float) -> None:
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
