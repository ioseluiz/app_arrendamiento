from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.models import Documento, TipoDocumento
from app.paths import DATA_DIR

PREVIEW_MAX_SIZE = QSize(360, 480)


class DocumentoPreviewPanel(QWidget):
    """Muestra una previsualización del documento seleccionado: imagen
    escalada para fotos, primera página renderizada para PDFs (con
    QPdfDocument, nativo de Qt, sin dependencias externas), o un mensaje
    genérico para el resto. Siempre ofrece abrirlo con la app predeterminada
    del sistema (única forma de ver PDFs de varias páginas completos)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.imagen = QLabel("Selecciona un documento para previsualizarlo.")
        self.imagen.setAlignment(Qt.AlignCenter)
        self.imagen.setWordWrap(True)
        self.imagen.setMinimumSize(220, 220)
        self.imagen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imagen.setStyleSheet(
            "QLabel { background-color: #f2f2f2; border: 1px solid #cfcfcf; color: #666; }"
        )

        self.nombre = QLabel("")
        self.nombre.setWordWrap(True)
        self.nombre.setStyleSheet("font-weight: bold;")

        self.btn_abrir = QPushButton("Abrir con la app predeterminada")
        self.btn_abrir.setEnabled(False)
        self.btn_abrir.clicked.connect(self._abrir)

        layout = QVBoxLayout(self)
        layout.addWidget(self.imagen, 1)
        layout.addWidget(self.nombre)
        layout.addWidget(self.btn_abrir)

        self._ruta_absoluta: Path | None = None
        self._pdf_doc: QPdfDocument | None = None  # referencia viva mientras se muestra

    def mostrar(self, documento: Documento | None) -> None:
        if documento is None:
            self.limpiar()
            return

        ruta = DATA_DIR / documento.ruta_archivo
        self._ruta_absoluta = ruta
        self.nombre.setText(documento.nombre_archivo)
        self.btn_abrir.setEnabled(ruta.exists())
        self._pdf_doc = None

        if not ruta.exists():
            self.imagen.setPixmap(QPixmap())
            self.imagen.setText("El archivo ya no está en disco.")
            return

        if documento.tipo == TipoDocumento.FOTO:
            self._mostrar_imagen(ruta)
        elif documento.tipo == TipoDocumento.PDF:
            self._mostrar_pdf(ruta)
        else:
            self._mostrar_generico(ruta)

    def limpiar(self) -> None:
        self._ruta_absoluta = None
        self._pdf_doc = None
        self.nombre.setText("")
        self.imagen.setPixmap(QPixmap())
        self.imagen.setText("Selecciona un documento para previsualizarlo.")
        self.btn_abrir.setEnabled(False)

    def _mostrar_imagen(self, ruta: Path) -> None:
        pixmap = QPixmap(str(ruta))
        if pixmap.isNull():
            self.imagen.setPixmap(QPixmap())
            self.imagen.setText("No se pudo leer la imagen.")
            return
        self.imagen.setText("")
        self.imagen.setPixmap(
            pixmap.scaled(PREVIEW_MAX_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _mostrar_pdf(self, ruta: Path) -> None:
        doc = QPdfDocument(self)
        doc.load(str(ruta))
        if doc.pageCount() == 0:
            self.imagen.setPixmap(QPixmap())
            self.imagen.setText("No se pudo leer el PDF.")
            return
        imagen = doc.render(0, PREVIEW_MAX_SIZE)
        if imagen.isNull():
            self.imagen.setPixmap(QPixmap())
            self.imagen.setText("No se pudo renderizar el PDF.")
            return
        self._pdf_doc = doc
        self.imagen.setText("")
        self.imagen.setPixmap(QPixmap.fromImage(imagen))

    def _mostrar_generico(self, ruta: Path) -> None:
        self.imagen.setPixmap(QPixmap())
        self.imagen.setText(f"Sin previsualización disponible.\n\n{ruta.name}")

    def _abrir(self) -> None:
        if self._ruta_absoluta and self._ruta_absoluta.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._ruta_absoluta)))
