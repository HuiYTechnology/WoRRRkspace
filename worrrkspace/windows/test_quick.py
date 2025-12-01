import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        central = QWidget()
        layout = QVBoxLayout()
        
        # Простая кнопка для теста
        btn = QPushButton("Тест")
        btn.clicked.connect(lambda: print("Кнопка работает!"))
        layout.addWidget(btn)
        
        # Ваши виджеты по одному
        try:
            from markdown_editor import MarkdownNoteTab
            md_tab = MarkdownNoteTab()
            layout.addWidget(md_tab)
            print("MarkdownNoteTab загружен")
        except Exception as e:
            print(f"MarkdownNoteTab ошибка: {e}")
            
        central.setLayout(layout)
        self.setCentralWidget(central)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())