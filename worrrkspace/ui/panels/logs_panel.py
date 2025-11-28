"""Это ебанная заглушка"""


from PyQt6.QtWidgets import QTextEdit
from base_panel import DraggableDockWidget

class LogsPanel(DraggableDockWidget):
    def __init__(self, parent=None):
        super().__init__("Логи", parent)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("Лог событий приложения...\n")
        self.setWidget(text)