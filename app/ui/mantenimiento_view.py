from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models import EntidadTipo, EstadoMantenimiento, Mantenimiento
from app.services import (
    DocumentoService,
    EquipoService,
    FiltroMantenimientos,
    MantenimientoService,
    ProveedorService,
    RecordatorioService,
    generar_reporte_mantenimientos,
    mantenimientos_completados_filtrados,
)
from app.ui.documento_view import DocumentosDeEntidadDialog

TICKETS_COLUMNS = [
    "ID",
    "Título",
    "Equipo",
    "Proveedor",
    "Estado",
    "Solicitud",
    "Completado",
    "Costo",
    "Documentos",
]
RECORDATORIOS_COLUMNS = ["Equipo", "Frecuencia (meses)", "Último mantenimiento", "Próxima fecha", "Situación"]
HISTORIAL_COLUMNS = ["Título", "Equipo", "Proveedor", "Fecha completado", "Costo"]


class MantenimientoFormDialog(QDialog):
    def __init__(
        self,
        apartamento_id: int,
        parent: QWidget | None = None,
        mantenimiento: Mantenimiento | None = None,
        equipo_id_sugerido: int | None = None,
        titulo_sugerido: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(
            "Nuevo mantenimiento" if mantenimiento is None else f"Editar mantenimiento #{mantenimiento.id}"
        )

        self.titulo = QLineEdit()
        self.descripcion = QPlainTextEdit()
        self.descripcion.setFixedHeight(80)

        self.equipo = QComboBox()
        self.equipo.addItem("(ninguno)", None)
        for equipo in EquipoService.listar_por_apartamento(apartamento_id):
            self.equipo.addItem(equipo.nombre, equipo.id)

        self.proveedor = QComboBox()
        self.proveedor.addItem("(sin asignar)", None)
        for proveedor in ProveedorService.listar():
            self.proveedor.addItem(proveedor.nombre, proveedor.id)

        self.estado = QComboBox()
        for estado in EstadoMantenimiento:
            self.estado.addItem(estado.value, estado)

        self.fecha_solicitud = QDateEdit(calendarPopup=True)
        self.fecha_solicitud.setDate(QDate.currentDate())

        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 1_000_000)
        self.costo.setDecimals(2)
        self.costo.setSpecialValueText("(sin especificar)")

        if mantenimiento is not None:
            self.titulo.setText(mantenimiento.titulo)
            self.descripcion.setPlainText(mantenimiento.descripcion or "")
            self.equipo.setCurrentIndex(self.equipo.findData(mantenimiento.equipo_id))
            self.proveedor.setCurrentIndex(self.proveedor.findData(mantenimiento.proveedor_id))
            self.estado.setCurrentIndex(self.estado.findData(mantenimiento.estado))
            fs = mantenimiento.fecha_solicitud
            self.fecha_solicitud.setDate(QDate(fs.year, fs.month, fs.day))
            self.costo.setValue(mantenimiento.costo or 0)
        else:
            if equipo_id_sugerido is not None:
                self.equipo.setCurrentIndex(self.equipo.findData(equipo_id_sugerido))
            if titulo_sugerido:
                self.titulo.setText(titulo_sugerido)

        form = QFormLayout()
        form.addRow("Título", self.titulo)
        form.addRow("Descripción", self.descripcion)
        form.addRow("Equipo", self.equipo)
        form.addRow("Proveedor", self.proveedor)
        form.addRow("Estado", self.estado)
        form.addRow("Fecha de solicitud", self.fecha_solicitud)
        form.addRow("Costo", self.costo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _validar_y_aceptar(self) -> None:
        if not self.titulo.text().strip():
            QMessageBox.warning(self, "Datos incompletos", "El título es obligatorio.")
            return
        self.accept()

    def datos(self) -> dict:
        return {
            "titulo": self.titulo.text().strip(),
            "descripcion": self.descripcion.toPlainText().strip() or None,
            "equipo_id": self.equipo.currentData(),
            "proveedor_id": self.proveedor.currentData(),
            "estado": self.estado.currentData(),
            "fecha_solicitud": self.fecha_solicitud.date().toPython(),
            "costo": self.costo.value() or None,
        }


class MarcarCompletadoDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Marcar como completado")

        self.fecha_completado = QDateEdit(calendarPopup=True)
        self.fecha_completado.setDate(QDate.currentDate())

        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 1_000_000)
        self.costo.setDecimals(2)
        self.costo.setSpecialValueText("(sin especificar)")

        form = QFormLayout()
        form.addRow("Fecha de finalización", self.fecha_completado)
        form.addRow("Costo", self.costo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def datos(self) -> dict:
        return {
            "fecha_completado": self.fecha_completado.date().toPython(),
            "costo": self.costo.value() or None,
        }


class TicketsMantenimientoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.tabla = QTableWidget(0, len(TICKETS_COLUMNS))
        self.tabla.setHorizontalHeaderLabels(TICKETS_COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_nuevo = QPushButton("Nuevo")
        btn_editar = QPushButton("Editar")
        btn_completado = QPushButton("Marcar completado")
        btn_documentos = QPushButton("Documentos...")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_completado.clicked.connect(self._marcar_completado)
        btn_documentos.clicked.connect(self._documentos)
        btn_eliminar.clicked.connect(self._eliminar)
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_nuevo)
        botones.addWidget(btn_editar)
        botones.addWidget(btn_completado)
        botones.addWidget(btn_documentos)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        mantenimientos = MantenimientoService.listar_por_apartamento(self.apartamento_id)
        self.tabla.setRowCount(0)
        for mant in mantenimientos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                str(mant.id),
                mant.titulo,
                mant.equipo.nombre if mant.equipo_id else "",
                mant.proveedor.nombre if mant.proveedor_id else "",
                mant.estado.value,
                mant.fecha_solicitud.isoformat(),
                mant.fecha_completado.isoformat() if mant.fecha_completado else "",
                f"{mant.costo:.2f}" if mant.costo is not None else "",
                str(len(DocumentoService.listar_por_entidad(EntidadTipo.MANTENIMIENTO, mant.id))),
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(row, col, QTableWidgetItem(valor))

    def _selected_id(self) -> int | None:
        row = self.tabla.currentRow()
        if row < 0:
            return None
        item = self.tabla.item(row, 0)
        return int(item.text()) if item else None

    def _nuevo(self) -> None:
        dialog = MantenimientoFormDialog(self.apartamento_id, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            MantenimientoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _editar(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Editar mantenimiento", "Selecciona un mantenimiento de la tabla.")
            return
        mant = MantenimientoService.obtener(mant_id)
        if mant is None:
            QMessageBox.warning(self, "Error", "El mantenimiento ya no existe.")
            self.refrescar()
            return
        dialog = MantenimientoFormDialog(self.apartamento_id, self, mant)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            MantenimientoService.actualizar(mant_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()

    def _marcar_completado(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Marcar completado", "Selecciona un mantenimiento de la tabla.")
            return
        dialog = MarcarCompletadoDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        MantenimientoService.marcar_completado(mant_id, **dialog.datos())
        self.refrescar()

    def _eliminar(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Eliminar mantenimiento", "Selecciona un mantenimiento de la tabla.")
            return
        respuesta = QMessageBox.question(
            self, "Eliminar mantenimiento", f"¿Eliminar el mantenimiento #{mant_id}?"
        )
        if respuesta != QMessageBox.Yes:
            return
        MantenimientoService.eliminar(mant_id)
        self.refrescar()

    def _documentos(self) -> None:
        mant_id = self._selected_id()
        if mant_id is None:
            QMessageBox.information(self, "Documentos", "Selecciona un mantenimiento de la tabla.")
            return
        mant = MantenimientoService.obtener(mant_id)
        if mant is None:
            QMessageBox.warning(self, "Error", "El mantenimiento ya no existe.")
            self.refrescar()
            return
        DocumentosDeEntidadDialog(EntidadTipo.MANTENIMIENTO, mant_id, mant.titulo, self).exec()


class RecordatoriosMantenimientoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.tabla = QTableWidget(0, len(RECORDATORIOS_COLUMNS))
        self.tabla.setHorizontalHeaderLabels(RECORDATORIOS_COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_crear_ticket = QPushButton("Crear ticket de mantenimiento")
        btn_crear_ticket.clicked.connect(self._crear_ticket)
        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_crear_ticket)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Equipos con frecuencia de mantenimiento preventivo definida (pestaña Equipos) "
                "que están vencidos o próximos a vencer (30 días)."
            )
        )
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def refrescar(self) -> None:
        recordatorios = RecordatorioService.proximos_mantenimientos(self.apartamento_id, dias=30)
        self.tabla.setRowCount(0)
        for r in recordatorios:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            situacion = (
                f"Vencido hace {-r.dias_restantes} días"
                if r.dias_restantes < 0
                else f"En {r.dias_restantes} días"
            )
            valores = [
                r.equipo_nombre,
                str(r.frecuencia_meses),
                r.ultimo_mantenimiento.isoformat() if r.ultimo_mantenimiento else "(nunca)",
                r.proxima_fecha.isoformat(),
                situacion,
            ]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.UserRole, r.equipo_id)
                self.tabla.setItem(row, col, item)

    def _selected_equipo_id(self) -> int | None:
        row = self.tabla.currentRow()
        if row < 0:
            return None
        item = self.tabla.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _crear_ticket(self) -> None:
        equipo_id = self._selected_equipo_id()
        if equipo_id is None:
            QMessageBox.information(self, "Crear ticket", "Selecciona un recordatorio de la tabla.")
            return
        equipo = EquipoService.obtener(equipo_id)
        titulo_sugerido = f"Mantenimiento preventivo: {equipo.nombre}" if equipo else None
        dialog = MantenimientoFormDialog(
            self.apartamento_id, self, equipo_id_sugerido=equipo_id, titulo_sugerido=titulo_sugerido
        )
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            MantenimientoService.crear(apartamento_id=self.apartamento_id, **dialog.datos())
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.refrescar()


class HistorialMantenimientoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.filtro_equipo = QComboBox()
        self.filtro_equipo.currentIndexChanged.connect(self.refrescar)

        self.filtro_proveedor = QComboBox()
        self.filtro_proveedor.currentIndexChanged.connect(self.refrescar)

        self.fecha_desde = QDateEdit(calendarPopup=True)
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-6))
        self.fecha_desde.setEnabled(False)
        self.fecha_desde.dateChanged.connect(self.refrescar)
        self.sin_fecha_desde = QCheckBox("Sin límite")
        self.sin_fecha_desde.setChecked(True)
        self.sin_fecha_desde.toggled.connect(lambda activo: self.fecha_desde.setDisabled(activo))
        self.sin_fecha_desde.toggled.connect(self.refrescar)

        self.fecha_hasta = QDateEdit(calendarPopup=True)
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setEnabled(False)
        self.fecha_hasta.dateChanged.connect(self.refrescar)
        self.sin_fecha_hasta = QCheckBox("Sin límite")
        self.sin_fecha_hasta.setChecked(True)
        self.sin_fecha_hasta.toggled.connect(lambda activo: self.fecha_hasta.setDisabled(activo))
        self.sin_fecha_hasta.toggled.connect(self.refrescar)

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("Equipo:"))
        filtros.addWidget(self.filtro_equipo)
        filtros.addWidget(QLabel("Proveedor:"))
        filtros.addWidget(self.filtro_proveedor)
        filtros.addWidget(QLabel("Desde:"))
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(self.sin_fecha_desde)
        filtros.addWidget(QLabel("Hasta:"))
        filtros.addWidget(self.fecha_hasta)
        filtros.addWidget(self.sin_fecha_hasta)
        filtros.addStretch()

        self.tabla = QTableWidget(0, len(HISTORIAL_COLUMNS))
        self.tabla.setHorizontalHeaderLabels(HISTORIAL_COLUMNS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)

        btn_generar_pdf = QPushButton("Generar reporte PDF...")
        btn_generar_pdf.clicked.connect(self._generar_reporte)
        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.clicked.connect(self.refrescar)

        botones = QHBoxLayout()
        botones.addWidget(btn_generar_pdf)
        botones.addStretch()
        botones.addWidget(btn_refrescar)

        layout = QVBoxLayout(self)
        layout.addLayout(filtros)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.refrescar()

    def _filtro_actual(self) -> FiltroMantenimientos:
        return FiltroMantenimientos(
            apartamento_id=self.apartamento_id,
            equipo_id=self.filtro_equipo.currentData(),
            proveedor_id=self.filtro_proveedor.currentData(),
            fecha_desde=None if self.sin_fecha_desde.isChecked() else self.fecha_desde.date().toPython(),
            fecha_hasta=None if self.sin_fecha_hasta.isChecked() else self.fecha_hasta.date().toPython(),
        )

    def _repoblar_combo(self, combo: QComboBox, etiqueta_todos: str, opciones: list[tuple[str, int]]) -> None:
        # Los equipos/proveedores pueden crearse en otra pestaña mientras esta
        # vista ya está construida; se repuebla en cada refrescar() en vez de
        # una sola vez en __init__, preservando la selección si sigue existiendo.
        seleccion_actual = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(etiqueta_todos, None)
        for etiqueta, valor_id in opciones:
            combo.addItem(etiqueta, valor_id)
        indice = combo.findData(seleccion_actual)
        combo.setCurrentIndex(indice if indice >= 0 else 0)
        combo.blockSignals(False)

    def refrescar(self) -> None:
        self._repoblar_combo(
            self.filtro_equipo,
            "Todos los equipos",
            [(e.nombre, e.id) for e in EquipoService.listar_por_apartamento(self.apartamento_id)],
        )
        self._repoblar_combo(
            self.filtro_proveedor,
            "Todos los proveedores",
            [(p.nombre, p.id) for p in ProveedorService.listar()],
        )

        historial = mantenimientos_completados_filtrados(self._filtro_actual())
        self.tabla.setRowCount(0)
        for mant in historial:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            valores = [
                mant.titulo,
                mant.equipo.nombre if mant.equipo_id else "",
                mant.proveedor.nombre if mant.proveedor_id else "",
                mant.fecha_completado.isoformat() if mant.fecha_completado else "",
                f"{mant.costo:.2f}" if mant.costo is not None else "",
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(row, col, QTableWidgetItem(valor))

    def _generar_reporte(self) -> None:
        filtro = self._filtro_actual()
        cantidad_preliminar = len(mantenimientos_completados_filtrados(filtro))
        if cantidad_preliminar == 0:
            QMessageBox.information(
                self, "Generar reporte", "No hay mantenimientos completados que coincidan con el filtro."
            )
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte de mantenimientos",
            str(Path.home() / "reporte_mantenimientos.pdf"),
            "PDF (*.pdf)",
        )
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        try:
            cantidad = generar_reporte_mantenimientos(filtro, Path(ruta))
        except Exception as exc:  # generación de PDF/fusión: variedad de fallos de E/S no enumerables
            QMessageBox.warning(self, "Error", f"No se pudo generar el reporte:\n{exc}")
            return

        respuesta = QMessageBox.question(
            self,
            "Reporte generado",
            f"Se generó el reporte con {cantidad} mantenimiento(s) en:\n{ruta}\n\n¿Abrirlo ahora?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if respuesta == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


class MantenimientoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.tickets_view = TicketsMantenimientoView(apartamento_id)
        self.recordatorios_view = RecordatoriosMantenimientoView(apartamento_id)
        self.historial_view = HistorialMantenimientoView(apartamento_id)

        self._tabs = QTabWidget()
        self._tabs.addTab(self.tickets_view, "Tickets")
        self._tabs.addTab(self.recordatorios_view, "Recordatorios preventivos")
        self._tabs.addTab(self.historial_view, "Historial")
        self._tabs.currentChanged.connect(self._al_cambiar_subtab)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)

    def _al_cambiar_subtab(self, index: int) -> None:
        self._tabs.widget(index).refrescar()

    def refrescar(self) -> None:
        self._tabs.currentWidget().refrescar()
