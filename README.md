# Arrendamiento App

Aplicación de escritorio (macOS) para gestionar el contrato de arrendamiento del apartamento: contrato, documentos (fotos/PDFs), mantenimiento, equipos, pagos de servicios (luz/agua/cable) y un modelo 3D interactivo con marcadores.

Ver el diseño completo en `docs/plan_gestion_arrendamiento.md`, `docs/der_arrendamiento.mermaid` y `docs/arquitectura_arrendamiento.mermaid`.

## Stack
- Python 3.11+
- PySide6 (UI) + QWebEngineView (visor 3D con three.js)
- SQLAlchemy + SQLite
- Pillow (imágenes), pypdf / pdf2image (PDFs)

## Estructura del proyecto
```
arrendamiento_app/
├── app/
│   ├── main.py
│   ├── ui/
│   ├── viewer3d/
│   ├── services/
│   ├── repositories/
│   └── models/
├── data/
│   ├── app.db
│   ├── documentos/
│   └── modelos_3d/
├── docs/
├── requirements.txt
└── README.md
```

## Setup

1. Clonar / ubicarse en la carpeta del proyecto:
   ```bash
   cd ~/Proyectos/arrendamiento_app
   ```

2. Crear y activar entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crear las carpetas de datos (si no existen):
   ```bash
   mkdir -p data/documentos data/modelos_3d
   ```

5. Ejecutar la app (como módulo, desde la raíz del proyecto — `python app/main.py` falla porque el código usa imports absolutos del paquete `app`):
   ```bash
   python -m app.main
   ```

## Dependencias (`requirements.txt`)
```
PySide6>=6.6
SQLAlchemy>=2.0
Pillow>=10.0
pypdf>=4.0
pdf2image>=1.17
alembic>=1.13
```

> Notas:
> - `pdf2image` requiere `poppler` instalado en el sistema (`brew install poppler`).
> - `PySide6-WebEngine` no se instala aparte: `QtWebEngineWidgets`, `QtWebChannel` y `QtCharts` (visor 3D y dashboard) ya vienen incluidos en `PySide6`/`PySide6-Addons`.

Para desarrollo (lint) instalar además:
```bash
pip install -r requirements-dev.txt
```

## Desarrollo

- **Lint**: `ruff check .` (configurado en `pyproject.toml`).
- **Chequeo de arranque**: `QT_QPA_PLATFORM=offscreen python scripts/smoke_check.py` — levanta la ventana principal sin mostrarla y valida que todas las pestañas cargan sin errores. No sustituye pruebas unitarias (todavía no hay suite de tests), pero atrapa errores de import/arranque.
- **CI**: `.github/workflows/ci.yml` corre lint + chequeo de arranque en cada push/PR a `main`.

## Versionado y releases

Los releases de GitHub se generan automáticamente al empujar un tag `vX.Y.Z`:
```bash
git tag v0.1.0
git push origin v0.1.0
```
Esto dispara `.github/workflows/release.yml`, que compila `Arrendamiento.app` en un runner macOS, lo comprime y lo adjunta al Release junto con notas autogeneradas a partir de los commits.

## Empaquetado para macOS

```bash
pip install -r requirements-build.txt
pyinstaller Arrendamiento.spec --clean --noconfirm
```

El resultado queda en `dist/Arrendamiento.app`. Notas importantes:

- **Dónde viven los datos**: la app empaquetada guarda la base de datos, los documentos y los modelos 3D en `~/Library/Application Support/Arrendamiento/`, **no** dentro del bundle (que puede no ser escribible y se reemplaza en cada reinstalación). Ver `app/paths.py`.
- **`app/viewer3d/`** (HTML/JS/three.js vendorizado) se empaqueta como recurso de solo lectura dentro del `.app`.
- **Sin firma de Developer ID ni notarización**: el `.app` queda con firma ad-hoc (la que aplica PyInstaller por defecto en Apple Silicon para poder ejecutarlo), pero no está firmado con un certificado de Apple Developer Program ni notarizado. Gatekeeper mostrará "no se puede verificar el desarrollador" al abrirlo por primera vez — click derecho → Abrir, o `xattr -cr Arrendamiento.app` para quitar el atributo de cuarentena. Firmar/notarizar de verdad requiere una cuenta de pago de Apple Developer Program, fuera del alcance de este repo.

## Roadmap (ver plan completo en docs/)
1. ✅ Modelos SQLAlchemy + CRUD básico (Contrato, Documento, Equipo, Mantenimiento, Pagos, Proveedores)
2. ✅ UI completa (PySide6) para todas las entidades, tema claro forzado (Fusion)
3. ✅ Visor 3D con marcadores (three.js + QWebChannel, servidor HTTP local embebido)
4. ✅ Reportes, dashboard con gráficos (QtCharts) y recordatorios de mantenimiento preventivo
5. ✅ Empaquetado `.app` distribuible (PyInstaller, ver sección arriba)
