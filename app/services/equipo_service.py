from __future__ import annotations

from datetime import date

from app.models import Equipo, EstadoEquipo, SessionLocal
from app.repositories import EquipoRepository


class EquipoService:
    @staticmethod
    def crear(
        apartamento_id: int,
        nombre: str,
        tipo: str,
        ubicacion: str | None = None,
        fecha_instalacion: date | None = None,
        estado: EstadoEquipo = EstadoEquipo.OPERATIVO,
        frecuencia_mantenimiento_meses: int | None = None,
    ) -> Equipo:
        with SessionLocal() as session:
            repo = EquipoRepository(session)
            equipo = repo.add(
                Equipo(
                    apartamento_id=apartamento_id,
                    nombre=nombre,
                    tipo=tipo,
                    ubicacion=ubicacion,
                    fecha_instalacion=fecha_instalacion,
                    estado=estado,
                    frecuencia_mantenimiento_meses=frecuencia_mantenimiento_meses,
                )
            )
            session.commit()
            return equipo

    @staticmethod
    def obtener(equipo_id: int) -> Equipo | None:
        with SessionLocal() as session:
            return EquipoRepository(session).get(equipo_id)

    @staticmethod
    def listar_por_apartamento(apartamento_id: int) -> list[Equipo]:
        with SessionLocal() as session:
            return EquipoRepository(session).list_by_apartamento(apartamento_id)

    @staticmethod
    def actualizar(equipo_id: int, **cambios) -> Equipo:
        with SessionLocal() as session:
            repo = EquipoRepository(session)
            equipo = repo.get(equipo_id)
            if equipo is None:
                raise ValueError(f"Equipo {equipo_id} no existe")
            for campo, valor in cambios.items():
                setattr(equipo, campo, valor)
            session.commit()
            return equipo

    @staticmethod
    def eliminar(equipo_id: int) -> None:
        with SessionLocal() as session:
            repo = EquipoRepository(session)
            equipo = repo.get(equipo_id)
            if equipo is None:
                raise ValueError(f"Equipo {equipo_id} no existe")
            repo.delete(equipo)
            session.commit()
