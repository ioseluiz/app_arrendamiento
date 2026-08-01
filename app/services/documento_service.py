from __future__ import annotations

from datetime import date

from app.models import Documento, EntidadTipo, SessionLocal, TipoDocumento
from app.repositories import DocumentoRepository


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
