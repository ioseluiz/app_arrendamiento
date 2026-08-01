from __future__ import annotations

import base64
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pypdf import PdfWriter
from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from app.models import EntidadTipo, Mantenimiento, TipoDocumento
from app.paths import DATA_DIR
from app.services.documento_service import DocumentoService
from app.services.equipo_service import EquipoService
from app.services.proveedor_service import ProveedorService
from app.services.reporte_service import ReporteService


@dataclass(frozen=True)
class FiltroMantenimientos:
    apartamento_id: int
    equipo_id: int | None = None
    proveedor_id: int | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None


def mantenimientos_completados_filtrados(filtro: FiltroMantenimientos) -> list[Mantenimiento]:
    return ReporteService.historial_mantenimientos(
        filtro.apartamento_id,
        equipo_id=filtro.equipo_id,
        proveedor_id=filtro.proveedor_id,
        fecha_desde=filtro.fecha_desde,
        fecha_hasta=filtro.fecha_hasta,
    )


def _imagen_a_data_uri(ruta: Path) -> str | None:
    if not ruta.exists():
        return None
    extension = ruta.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if extension in ("jpg", "jpeg") else extension
    try:
        datos = ruta.read_bytes()
    except OSError:
        return None
    return f"data:image/{mime};base64,{base64.b64encode(datos).decode('ascii')}"


def _html_portada(filtro: FiltroMantenimientos, cantidad: int) -> str:
    partes = ["<h1>Reporte de mantenimientos</h1>", f"<p>Generado el {date.today().isoformat()}</p>"]
    if filtro.equipo_id is not None:
        equipo = EquipoService.obtener(filtro.equipo_id)
        if equipo:
            partes.append(f"<p><b>Equipo:</b> {equipo.nombre}</p>")
    if filtro.proveedor_id is not None:
        proveedor = ProveedorService.obtener(filtro.proveedor_id)
        if proveedor:
            partes.append(f"<p><b>Proveedor:</b> {proveedor.nombre}</p>")
    if filtro.fecha_desde is not None:
        partes.append(f"<p><b>Desde:</b> {filtro.fecha_desde.isoformat()}</p>")
    if filtro.fecha_hasta is not None:
        partes.append(f"<p><b>Hasta:</b> {filtro.fecha_hasta.isoformat()}</p>")
    partes.append(f"<p><b>Mantenimientos incluidos:</b> {cantidad}</p>")
    return "".join(partes)


def _html_detalle_mantenimiento(mant: Mantenimiento, fotos: list[Path], tiene_factura: bool) -> str:
    equipo = mant.equipo.nombre if mant.equipo_id else "—"
    proveedor = mant.proveedor.nombre if mant.proveedor_id else "—"
    fecha = (mant.fecha_completado or mant.fecha_solicitud).isoformat()
    costo = f"${mant.costo:,.2f}" if mant.costo is not None else "—"
    descripcion = (mant.descripcion or "").replace("\n", "<br/>")

    imagenes_html = "".join(
        f'<img src="{uri}" width="240" style="margin:6px;" />'
        for ruta in fotos
        if (uri := _imagen_a_data_uri(ruta)) is not None
    )
    nota_factura = "<p><i>Factura adjunta a continuación.</i></p>" if tiene_factura else ""

    return f"""
    <h2>{mant.titulo}</h2>
    <table cellpadding="4">
      <tr><td><b>Fecha</b></td><td>{fecha}</td></tr>
      <tr><td><b>Equipo</b></td><td>{equipo}</td></tr>
      <tr><td><b>Proveedor</b></td><td>{proveedor}</td></tr>
      <tr><td><b>Costo</b></td><td>{costo}</td></tr>
    </table>
    <p>{descripcion}</p>
    <div>{imagenes_html}</div>
    {nota_factura}
    """


def _renderizar_html_a_pdf(html: str, ruta_salida: Path) -> None:
    documento = QTextDocument()
    documento.setHtml(html)

    printer = QPrinter()
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(ruta_salida))
    printer.setPageSize(QPageSize(QPageSize.Letter))
    documento.print_(printer)


def generar_reporte_mantenimientos(filtro: FiltroMantenimientos, ruta_salida: Path) -> int:
    """Genera un PDF consolidado: portada + detalle de cada mantenimiento
    completado que cumpla el filtro (con sus fotos incrustadas), seguido de
    las páginas reales de su factura adjunta (si tiene). Devuelve la
    cantidad de mantenimientos incluidos."""
    mantenimientos = mantenimientos_completados_filtrados(filtro)

    with tempfile.TemporaryDirectory(prefix="arrendamiento_reporte_") as tmp:
        tmp_dir = Path(tmp)
        writer = PdfWriter()

        portada_pdf = tmp_dir / "portada.pdf"
        _renderizar_html_a_pdf(_html_portada(filtro, len(mantenimientos)), portada_pdf)
        writer.append(str(portada_pdf))

        for indice, mant in enumerate(mantenimientos):
            documentos = DocumentoService.listar_por_entidad(EntidadTipo.MANTENIMIENTO, mant.id)
            fotos = [DATA_DIR / d.ruta_archivo for d in documentos if d.tipo == TipoDocumento.FOTO]
            facturas = [DATA_DIR / d.ruta_archivo for d in documentos if d.tipo == TipoDocumento.PDF]

            detalle_pdf = tmp_dir / f"detalle_{indice}.pdf"
            _renderizar_html_a_pdf(
                _html_detalle_mantenimiento(mant, fotos, tiene_factura=bool(facturas)), detalle_pdf
            )
            writer.append(str(detalle_pdf))

            for factura in facturas:
                if factura.exists():
                    writer.append(str(factura))

        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        writer.write(str(ruta_salida))
        writer.close()

    return len(mantenimientos)
