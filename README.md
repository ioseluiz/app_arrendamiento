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

5. Ejecutar la app:
   ```bash
   python app/main.py
   ```

## requirements.txt (sugerido)
```
PySide6>=6.6
PySide6-WebEngine>=6.6
SQLAlchemy>=2.0
Pillow>=10.0
pypdf>=4.0
pdf2image>=1.17
alembic>=1.13
```

> Nota: `pdf2image` requiere `poppler` instalado en el sistema (`brew install poppler`).

## Empaquetado para macOS (fase final)
```bash
pip install pyinstaller
pyinstaller --windowed --name "Arrendamiento" app/main.py
```

## Roadmap (ver plan completo en docs/)
1. Modelos SQLAlchemy + CRUD básico (Contrato, Documento, Equipo)
2. Mantenimiento y pagos de servicios
3. Visor 3D con marcadores (three.js + QWebChannel)
4. Reportes (gastos, mantenimiento pendiente, vencimientos)
5. Empaquetado `.app` distribuible
