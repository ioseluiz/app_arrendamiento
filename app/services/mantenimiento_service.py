from __future__ import annotations

from datetime import date

from app.models import EstadoMantenimiento, Mantenimiento, SessionLocal
from app.repositories import MantenimientoRepository


class MantenimientoService:
    @staticmethod
    def crear(
        apartamento_id: int,
        titulo: str,
        fecha_solicitud: date | None = None,
        equipo_id: int | None = None,
        proveedor_id: int | None = None,
        descripcion: str | None = None,
        estado: EstadoMantenimiento = EstadoMantenimiento.PENDIENTE,
        costo: float | None = None,
    ) -> Mantenimiento:
        with SessionLocal() as session:
            repo = MantenimientoRepository(session)
            mantenimiento = repo.add(
                Mantenimiento(
                    apartamento_id=apartamento_id,
                    equipo_id=equipo_id,
                    proveedor_id=proveedor_id,
                    titulo=titulo,
                    descripcion=descripcion,
                    estado=estado,
                    fecha_solicitud=fecha_solicitud or date.today(),
                    costo=costo,
                )
            )
            session.commit()
            return mantenimiento

    @staticmethod
    def obtener(mantenimiento_id: int) -> Mantenimiento | None:
        with SessionLocal() as session:
            return MantenimientoRepository(session).get(mantenimiento_id)

    @staticmethod
    def listar_por_apartamento(apartamento_id: int) -> list[Mantenimiento]:
        with SessionLocal() as session:
            return MantenimientoRepository(session).list_by_apartamento(apartamento_id)

    @staticmethod
    def listar_por_estado(estado: EstadoMantenimiento) -> list[Mantenimiento]:
        with SessionLocal() as session:
            return MantenimientoRepository(session).list_by_estado(estado)

    @staticmethod
    def actualizar(mantenimiento_id: int, **cambios) -> Mantenimiento:
        with SessionLocal() as session:
            repo = MantenimientoRepository(session)
            mantenimiento = repo.get(mantenimiento_id)
            if mantenimiento is None:
                raise ValueError(f"Mantenimiento {mantenimiento_id} no existe")
            for campo, valor in cambios.items():
                setattr(mantenimiento, campo, valor)
            session.commit()
            return mantenimiento

    @staticmethod
    def marcar_completado(
        mantenimiento_id: int,
        fecha_completado: date | None = None,
        costo: float | None = None,
    ) -> Mantenimiento:
        with SessionLocal() as session:
            repo = MantenimientoRepository(session)
            mantenimiento = repo.get(mantenimiento_id)
            if mantenimiento is None:
                raise ValueError(f"Mantenimiento {mantenimiento_id} no existe")
            mantenimiento.estado = EstadoMantenimiento.COMPLETADO
            mantenimiento.fecha_completado = fecha_completado or date.today()
            if costo is not None:
                mantenimiento.costo = costo
            session.commit()
            return mantenimiento

    @staticmethod
    def eliminar(mantenimiento_id: int) -> None:
        with SessionLocal() as session:
            repo = MantenimientoRepository(session)
            mantenimiento = repo.get(mantenimiento_id)
            if mantenimiento is None:
                raise ValueError(f"Mantenimiento {mantenimiento_id} no existe")
            repo.delete(mantenimiento)
            session.commit()
