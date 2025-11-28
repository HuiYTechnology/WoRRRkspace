"""Это ебанная заглушка"""


from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Профиль")
        self.setMinimumSize(320, 200)
        layout = QVBoxLayout()
        lbl = QLabel("Здесь будут иль нет")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        btn = QPushButton("Закрыть")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)