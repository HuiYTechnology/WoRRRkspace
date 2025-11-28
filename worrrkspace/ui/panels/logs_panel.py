"""Это ебанная заглушка"""


from PyQt6.QtWidgets import QTextEdit
try:
    from .base_panel import BasePanel
except ImportError:
    from base_panel import BasePanel

class LogsPanel(DraggableDockWidget):
    def __init__(self, parent=None):
        super().__init__("Логи", parent)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("Лог событий приложения...\n")
        self.setWidget(text)