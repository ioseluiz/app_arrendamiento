"""Chequeo de humo para CI: la app debe arrancar (offscreen) sin excepciones.

No sustituye pruebas unitarias; solo detecta errores de import/arranque
(modelos, servicios, UI) antes de fusionar un cambio.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from app.models import init_db
from app.ui.main_window import MainWindow

PESTANAS_ESPERADAS = 10


def main() -> None:
    init_db()
    _app = QApplication(sys.argv)
    window = MainWindow()

    conteo = window.tabs.count()
    nombres = [window.tabs.tabText(i) for i in range(conteo)]
    if conteo != PESTANAS_ESPERADAS:
        raise SystemExit(f"Se esperaban {PESTANAS_ESPERADAS} pestañas, hay {conteo}: {nombres}")

    for i in range(conteo):
        window.tabs.setCurrentIndex(i)

    print(f"OK: MainWindow arrancó con {conteo} pestañas: {nombres}")


if __name__ == "__main__":
    main()
