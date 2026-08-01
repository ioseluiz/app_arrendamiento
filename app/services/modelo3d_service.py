from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from app.models import EntidadTipo, Marcador, Modelo3D, SessionLocal
from app.models.base import DATA_DIR
from app.repositories import MarcadorRepository, Modelo3DRepository

MODELOS_DIR = DATA_DIR / "modelos_3d"
PROJECT_ROOT = DATA_DIR.parent
FORMATOS_SOPORTADOS = {".glb", ".gltf"}


class Modelo3DService:
    @staticmethod
    def obtener_por_apartamento(apartamento_id: int) -> Modelo3D | None:
        with SessionLocal() as session:
            return Modelo3DRepository(session).get_by_apartamento(apartamento_id)

    @staticmethod
    def importar_modelo(apartamento_id: int, ruta_origen: Path) -> Modelo3D:
        if ruta_origen.suffix.lower() not in FORMATOS_SOPORTADOS:
            raise ValueError("El modelo debe ser un archivo .glb o .gltf")

        MODELOS_DIR.mkdir(parents=True, exist_ok=True)
        destino = MODELOS_DIR / ruta_origen.name
        contador = 1
        while destino.exists():
            destino = MODELOS_DIR / f"{ruta_origen.stem}_{contador}{ruta_origen.suffix}"
            contador += 1
        shutil.copy2(ruta_origen, destino)
        ruta_relativa = str(destino.relative_to(PROJECT_ROOT))

        with SessionLocal() as session:
            repo = Modelo3DRepository(session)
            modelo = repo.get_by_apartamento(apartamento_id)
            if modelo is None:
                modelo = repo.add(
                    Modelo3D(
                        apartamento_id=apartamento_id,
                        archivo_modelo=ruta_relativa,
                        formato=ruta_origen.suffix.lower().lstrip("."),
                        fecha_actualizacion=date.today(),
                    )
                )
            else:
                modelo.archivo_modelo = ruta_relativa
                modelo.formato = ruta_origen.suffix.lower().lstrip(".")
                modelo.fecha_actualizacion = date.today()
            session.commit()
            return modelo

    @staticmethod
    def crear_marcador(
        modelo_3d_id: int,
        pos_x: float,
        pos_y: float,
        pos_z: float,
        etiqueta: str,
        tipo_referencia: EntidadTipo | None = None,
        referencia_id: int | None = None,
    ) -> Marcador:
        with SessionLocal() as session:
            repo = MarcadorRepository(session)
            marcador = repo.add(
                Marcador(
                    modelo_3d_id=modelo_3d_id,
                    pos_x=pos_x,
                    pos_y=pos_y,
                    pos_z=pos_z,
                    etiqueta=etiqueta,
                    tipo_referencia=tipo_referencia,
                    referencia_id=referencia_id,
                )
            )
            session.commit()
            return marcador

    @staticmethod
    def obtener_marcador(marcador_id: int) -> Marcador | None:
        with SessionLocal() as session:
            return MarcadorRepository(session).get(marcador_id)

    @staticmethod
    def listar_marcadores(modelo_3d_id: int) -> list[Marcador]:
        with SessionLocal() as session:
            return MarcadorRepository(session).list_by_modelo(modelo_3d_id)

    @staticmethod
    def eliminar_marcador(marcador_id: int) -> None:
        with SessionLocal() as session:
            repo = MarcadorRepository(session)
            marcador = repo.get(marcador_id)
            if marcador is None:
                raise ValueError(f"Marcador {marcador_id} no existe")
            repo.delete(marcador)
            session.commit()
