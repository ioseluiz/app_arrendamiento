from __future__ import annotations

import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    # Bundle de PyInstaller (onedir u onefile): sys._MEIPASS es la carpeta
    # donde el bootloader deja los recursos empaquetados (datas), sea un
    # .app en macOS o un ejecutable único. Es de solo lectura.
    RESOURCES_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Los datos del usuario (BD, documentos, modelos 3D) no pueden vivir
    # dentro del bundle: no es garantizado que sea escribible (firma/
    # notarización) y se perdería al reinstalar la app.
    DATA_DIR = Path.home() / "Library" / "Application Support" / "Arrendamiento"
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    RESOURCES_DIR = PROJECT_ROOT
    DATA_DIR = PROJECT_ROOT / "data"

DB_PATH = DATA_DIR / "app.db"
VIEWER3D_DIR = RESOURCES_DIR / "app" / "viewer3d"
