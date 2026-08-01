from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from app.models import Documento, EntidadTipo, SessionLocal, TipoDocumento
from app.paths import DATA_DIR
from app.repositories import DocumentoRepository

DOCUMENTOS_DIR = DATA_DIR / "documentos"
EXTENSIONES_FOTO = {".jpg", ".jpeg", ".png", ".heic", ".gif"}


def _inferir_tipo(ruta: Path) -> TipoDocumento:
    sufijo = ruta.suffix.lower()
    if sufijo == ".pdf":
        return TipoDocumento.PDF
    if sufijo in EXTENSIONES_FOTO:
        return TipoDocumento.FOTO
    return TipoDocumento.OTRO


class DocumentoService:
    @staticmethod
    def crear(
        tipo: TipoDocumento,
        nombre_archivo: str,
        ruta_archivo: str,
        entidad_tipo: EntidadTipo,
        entidad_id: int,
        fecha_subida: date | None = None,
    ) -> Documento:
        with SessionLocal() as session:
            repo = DocumentoRepository(session)
            documento = repo.add(
                Documento(
                    tipo=tipo,
                    nombre_archivo=nombre_archivo,
                    ruta_archivo=ruta_archivo,
                    fecha_subida=fecha_subida or date.today(),
                    entidad_tipo=entidad_tipo,
                    entidad_id=entidad_id,
                )
            )
            session.commit()
            return documento

    @staticmethod
    def adjuntar(
        entidad_tipo: EntidadTipo,
        entidad_id: int,
        ruta_origen: Path,
        tipo: TipoDocumento | None = None,
        fecha_subida: date | None = None,
    ) -> Documento:
        """Copia ruta_origen a DATA_DIR/documentos (evitando colisiones de
        nombre) y crea el registro vinculado a la entidad indicada. Si no se
        especifica tipo, se infiere de la extensión del archivo."""
        DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
        destino = DOCUMENTOS_DIR / ruta_origen.name
        contador = 1
        while destino.exists():
            destino = DOCUMENTOS_DIR / f"{ruta_origen.stem}_{contador}{ruta_origen.suffix}"
            contador += 1
        shutil.copy2(ruta_origen, destino)

        return DocumentoService.crear(
            tipo=tipo or _inferir_tipo(ruta_origen),
            nombre_archivo=ruta_origen.name,
            ruta_archivo=str(destino.relative_to(DATA_DIR)),
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            fecha_subida=fecha_subida,
        )

    @staticmethod
    def obtener(documento_id: int) -> Documento | None:
        with SessionLocal() as session:
            return DocumentoRepository(session).get(documento_id)

    @staticmethod
    def listar() -> list[Documento]:
        with SessionLocal() as session:
            return DocumentoRepository(session).list()

    @staticmethod
    def listar_por_entidad(entidad_tipo: EntidadTipo, entidad_id: int) -> list[Documento]:
        with SessionLocal() as session:
            return DocumentoRepository(session).list_by_entidad(entidad_tipo, entidad_id)

    @staticmethod
    def eliminar(documento_id: int) -> None:
        with SessionLocal() as session:
            repo = DocumentoRepository(session)
            documento = repo.get(documento_id)
            if documento is None:
                raise ValueError(f"Documento {documento_id} no existe")
            repo.delete(documento)
            session.commit()
