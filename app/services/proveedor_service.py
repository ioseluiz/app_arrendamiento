from __future__ import annotations

from app.models import Proveedor, SessionLocal
from app.repositories import ProveedorRepository


class ProveedorService:
    @staticmethod
    def crear(
        nombre: str,
        tipo_servicio: str,
        telefono: str | None = None,
        email: str | None = None,
    ) -> Proveedor:
        with SessionLocal() as session:
            repo = ProveedorRepository(session)
            proveedor = repo.add(
                Proveedor(
                    nombre=nombre,
                    tipo_servicio=tipo_servicio,
                    telefono=telefono,
                    email=email,
                )
            )
            session.commit()
            return proveedor

    @staticmethod
    def obtener(proveedor_id: int) -> Proveedor | None:
        with SessionLocal() as session:
            return ProveedorRepository(session).get(proveedor_id)

    @staticmethod
    def listar() -> list[Proveedor]:
        with SessionLocal() as session:
            return ProveedorRepository(session).list()

    @staticmethod
    def actualizar(proveedor_id: int, **cambios) -> Proveedor:
        with SessionLocal() as session:
            repo = ProveedorRepository(session)
            proveedor = repo.get(proveedor_id)
            if proveedor is None:
                raise ValueError(f"Proveedor {proveedor_id} no existe")
            for campo, valor in cambios.items():
                setattr(proveedor, campo, valor)
            session.commit()
            return proveedor

    @staticmethod
    def eliminar(proveedor_id: int) -> None:
        with SessionLocal() as session:
            repo = ProveedorRepository(session)
            proveedor = repo.get(proveedor_id)
            if proveedor is None:
                raise ValueError(f"Proveedor {proveedor_id} no existe")
            repo.delete(proveedor)
            session.commit()
