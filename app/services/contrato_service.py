from __future__ import annotations

from datetime import date

from app.models import Contrato, EstadoContrato, SessionLocal
from app.repositories import ContratoRepository


class ContratoService:
    @staticmethod
    def crear(
        apartamento_id: int,
        fecha_inicio: date,
        monto_mensual: float,
        arrendador: str,
        arrendatario: str,
        fecha_fin: date | None = None,
        estado: EstadoContrato = EstadoContrato.ACTIVO,
    ) -> Contrato:
        ContratoService._validar(fecha_inicio, fecha_fin, monto_mensual)
        with SessionLocal() as session:
            repo = ContratoRepository(session)
            contrato = repo.add(
                Contrato(
                    apartamento_id=apartamento_id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    monto_mensual=monto_mensual,
                    arrendador=arrendador,
                    arrendatario=arrendatario,
                    estado=estado,
                )
            )
            session.commit()
            return contrato

    @staticmethod
    def obtener(contrato_id: int) -> Contrato | None:
        with SessionLocal() as session:
            return ContratoRepository(session).get(contrato_id)

    @staticmethod
    def listar_por_apartamento(apartamento_id: int) -> list[Contrato]:
        with SessionLocal() as session:
            return ContratoRepository(session).list_by_apartamento(apartamento_id)

    @staticmethod
    def actualizar(contrato_id: int, **cambios) -> Contrato:
        with SessionLocal() as session:
            repo = ContratoRepository(session)
            contrato = repo.get(contrato_id)
            if contrato is None:
                raise ValueError(f"Contrato {contrato_id} no existe")
            for campo, valor in cambios.items():
                setattr(contrato, campo, valor)
            ContratoService._validar(contrato.fecha_inicio, contrato.fecha_fin, contrato.monto_mensual)
            session.commit()
            return contrato

    @staticmethod
    def eliminar(contrato_id: int) -> None:
        with SessionLocal() as session:
            repo = ContratoRepository(session)
            contrato = repo.get(contrato_id)
            if contrato is None:
                raise ValueError(f"Contrato {contrato_id} no existe")
            repo.delete(contrato)
            session.commit()

    @staticmethod
    def _validar(fecha_inicio: date, fecha_fin: date | None, monto_mensual: float) -> None:
        if monto_mensual <= 0:
            raise ValueError("El monto mensual debe ser mayor que cero")
        if fecha_fin is not None and fecha_fin < fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio")
