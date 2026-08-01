from __future__ import annotations

from app.models import Apartamento, SessionLocal
from app.repositories import ApartamentoRepository


class ApartamentoService:
    @staticmethod
    def crear(
        direccion: str,
        area_m2: float | None = None,
        habitaciones: int | None = None,
        banos: int | None = None,
    ) -> Apartamento:
        with SessionLocal() as session:
            repo = ApartamentoRepository(session)
            apartamento = repo.add(
                Apartamento(
                    direccion=direccion,
                    area_m2=area_m2,
                    habitaciones=habitaciones,
                    banos=banos,
                )
            )
            session.commit()
            return apartamento

    @staticmethod
    def obtener(apartamento_id: int) -> Apartamento | None:
        with SessionLocal() as session:
            return ApartamentoRepository(session).get(apartamento_id)

    @staticmethod
    def listar() -> list[Apartamento]:
        with SessionLocal() as session:
            return ApartamentoRepository(session).list()

    @staticmethod
    def actualizar(apartamento_id: int, **cambios) -> Apartamento:
        with SessionLocal() as session:
            repo = ApartamentoRepository(session)
            apartamento = repo.get(apartamento_id)
            if apartamento is None:
                raise ValueError(f"Apartamento {apartamento_id} no existe")
            for campo, valor in cambios.items():
                setattr(apartamento, campo, valor)
            session.commit()
            return apartamento

    @staticmethod
    def eliminar(apartamento_id: int) -> None:
        with SessionLocal() as session:
            repo = ApartamentoRepository(session)
            apartamento = repo.get(apartamento_id)
            if apartamento is None:
                raise ValueError(f"Apartamento {apartamento_id} no existe")
            repo.delete(apartamento)
            session.commit()
