from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.services import ApartamentoService


class ApartamentoView(QWidget):
    def __init__(self, apartamento_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.apartamento_id = apartamento_id

        self.direccion = QLineEdit()

        self.area_m2 = QDoubleSpinBox()
        self.area_m2.setRange(0, 10_000)
        self.area_m2.setDecimals(1)
        self.area_m2.setSuffix(" m²")
        self.area_m2.setSpecialValueText("(sin especificar)")

        self.habitaciones = QSpinBox()
        self.habitaciones.setRange(0, 20)
        self.habitaciones.setSpecialValueText("(sin especificar)")

        self.banos = QSpinBox()
        self.banos.setRange(0, 20)
        self.banos.setSpecialValueText("(sin especificar)")

        form = QFormLayout()
        form.addRow("Dirección", self.direccion)
        form.addRow("Área", self.area_m2)
        form.addRow("Habitaciones", self.habitaciones)
        form.addRow("Baños", self.banos)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._guardar)
        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(btn_guardar)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(botones)
        layout.addStretch()

        self._cargar()

    def _cargar(self) -> None:
        apartamento = ApartamentoService.obtener(self.apartamento_id)
        if apartamento is None:
            return
        self.direccion.setText(apartamento.direccion)
        self.area_m2.setValue(apartamento.area_m2 or 0)
        self.habitaciones.setValue(apartamento.habitaciones or 0)
        self.banos.setValue(apartamento.banos or 0)

    def _guardar(self) -> None:
        direccion = self.direccion.text().strip()
        if not direccion:
            QMessageBox.warning(self, "Datos incompletos", "La dirección es obligatoria.")
            return
        try:
            ApartamentoService.actualizar(
                self.apartamento_id,
                direccion=direccion,
                area_m2=self.area_m2.value() or None,
                habitaciones=self.habitaciones.value() or None,
                banos=self.banos.value() or None,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        QMessageBox.information(self, "Apartamento", "Datos guardados correctamente.")
