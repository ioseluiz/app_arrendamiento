# Plan de Diseño: App de Gestión de Arrendamiento

## 1. Objetivo
Aplicación de escritorio (macOS) para gestionar el contrato de arrendamiento de tu apartamento: documentos, mantenimiento, equipos, pagos de servicios y un modelo 3D interactivo para ubicar reparaciones.

## 2. Requisitos funcionales
- **Contrato**: registrar datos del contrato (fechas, monto, arrendador/arrendatario) y adjuntar el PDF firmado.
- **Documentos**: subir fotos y PDFs, asociarlos a contrato, equipo, mantenimiento o pago.
- **Modelo 3D**: cargar/visualizar un modelo 3D del apartamento y colocar marcadores (pines) sobre puntos específicos (ej. "grifo cocina", "aire acondicionado sala") vinculados a tareas de mantenimiento o equipos.
- **Mantenimiento**: crear tareas ("arreglar/arreglado"), estado (pendiente/en progreso/completado), costo, proveedor, fotos antes/después.
- **Equipos**: inventario de equipos del apartamento (AC, calentador, nevera, etc.) con historial de mantenimiento.
- **Pagos de servicios**: luz, agua, cable/internet — monto, período, fecha de vencimiento/pago, comprobante adjunto.
- **Proveedores/contactos**: técnicos, compañías de servicio.

## 3. Stack tecnológico (Python, macOS)
| Capa | Tecnología | Motivo |
|---|---|---|
| UI de escritorio | **PySide6** (Qt) | Nativo en macOS, widgets robustos, soporte para `QWebEngineView` |
| Visor 3D | **three.js** embebido vía `QWebEngineView` | Python no tiene un motor 3D interactivo maduro; three.js dentro de un WebView es el enfoque más práctico y flexible (soporta .glb/.gltf, raycasting para clics en el modelo) |
| Base de datos | **SQLite + SQLAlchemy (ORM)** | Local, sin servidor, ideal para app de un solo usuario |
| Manejo de PDFs | `pypdf` / `pdf2image` (miniaturas) | Adjuntar y previsualizar contratos y facturas |
| Manejo de imágenes | `Pillow` | Miniaturas de fotos |
| Empaquetado macOS | `PyInstaller` o `briefcase` | Generar app `.app` nativa |

## 4. Estructura de carpetas sugerida
```
arrendamiento_app/
├── app/
│   ├── main.py
│   ├── ui/                 # Vistas PySide6 (.py o .ui)
│   ├── viewer3d/            # HTML/JS three.js embebido
│   ├── services/            # Lógica de negocio
│   ├── repositories/        # Acceso a datos (SQLAlchemy)
│   └── models/              # Modelos ORM
├── data/
│   ├── app.db               # SQLite
│   ├── documentos/          # PDFs y fotos subidas
│   └── modelos_3d/          # Archivos .glb/.gltf
└── requirements.txt
```

## 5. Fases de desarrollo sugeridas
1. **Fase 1 – Base de datos y CRUD básico**: contrato, documentos, equipos.
2. **Fase 2 – Mantenimiento y pagos**: tareas, estados, pagos de servicios.
3. **Fase 3 – Visor 3D**: cargar modelo, colocar y editar marcadores, vincularlos a mantenimiento/equipos.
4. **Fase 4 – Reportes**: historial de gastos, mantenimiento pendiente, alertas de pagos próximos a vencer.
5. **Fase 5 – Empaquetado**: generar `.app` distribuible para tu MacBook Pro.

## 6. Notas sobre el modelo 3D
- El modelo 3D (creado en Blender, SketchUp o escaneado con apps como Polycam) se exporta a **.glb/.gltf**.
- Se muestra dentro de la app usando three.js en un `QWebEngineView`.
- Cada "marcador" es un punto (x,y,z) sobre el modelo; al hacer clic se abre el detalle del equipo o tarea de mantenimiento asociada.
- La comunicación entre Python y el JS del visor se hace con `QWebChannel` (Python ↔ JavaScript bridge).

## 7. Diagramas
Ver archivos adjuntos:
- `der_arrendamiento.mermaid` → Diagrama de Entidad-Relación
- `arquitectura_arrendamiento.mermaid` → Diagrama de Arquitectura
