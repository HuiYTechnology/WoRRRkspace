from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from .base_panel import DraggableDockWidget

class ToolsPanel(DraggableDockWidget):
    def __init__(self, parent=None):
        super().__init__("Инструменты", parent)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.btn_table = QPushButton("Новая таблица")
        self.btn_note = QPushButton("Новая заметка")
        self.btn_chart = QPushButton("Новый граф")
        self.btn_task = QPushButton("Новая задача")
        self.btn_diagramm = QPushButton("Новая Диаграмма")

        layout.addWidget(self.btn_table)
        layout.addWidget(self.btn_note)
        layout.addWidget(self.btn_chart)
        layout.addWidget(self.btn_task)
        layout.addWidget(self.btn_diagramm)
        layout.addStretch()
        self.setWidget(container)