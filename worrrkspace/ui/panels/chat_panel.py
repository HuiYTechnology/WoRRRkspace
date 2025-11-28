"""Это ебанная заглушка"""


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit
try:
    from .base_panel import DraggableDockWidget
except ImportError:
    from base_panel import DraggableDockWidget

class ChatPanel(DraggableDockWidget):
    def __init__(self, parent=None):
        super().__init__("Чат", parent)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Напишите сообщение и нажмите Enter...")
        layout.addWidget(self.history)
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._on_send)
        self.setWidget(container)

    def _on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.history.append(f"Вы: {text}")
        self.history.append("ИИ: (заглушка ответа)")
        self.input.clear()