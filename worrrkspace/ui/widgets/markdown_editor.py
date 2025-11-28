"""Это ебанная заглушка. Использующая не оч корректные решения"""


import markdown
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor


class MarkdownEditor(QWidget):
    """Виджет для редактирования Markdown с предпросмотром"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Введите ваш Markdown текст здесь...")

        font = QFont("Courier New", 10)
        self.editor.setFont(font)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Предпросмотр Markdown появится здесь...")

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([400, 400])

        layout.addWidget(self.splitter)

    def setup_connections(self):
        self.editor.textChanged.connect(self.update_preview)

    def update_preview(self):
        markdown_text = self.editor.toPlainText()
        if markdown_text.strip():
            try:
                html = markdown.markdown(
                    markdown_text,
                    extensions=['extra', 'codehilite', 'tables']
                )
                styled_html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
                        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
                        blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; margin-left: 0; color: #666; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    {html}
                </body>
                </html>
                """
                self.preview.setHtml(styled_html)
            except Exception as e:
                self.preview.setPlainText(f"Ошибка преобразования Markdown: {str(e)}")
        else:
            self.preview.clear()

    def set_markdown(self, text):
        self.editor.setPlainText(text)

    def get_markdown(self):
        return self.editor.toPlainText()


class MarkdownNoteTab(QWidget):
    """Вкладка для работы с Markdown заметками"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        format_container = QHBoxLayout()
        format_container.setSpacing(2)

        self.btn_bold = QPushButton("B")
        self.btn_italic = QPushButton("I")
        self.btn_code = QPushButton("</>")
        self.btn_heading1 = QPushButton("H1")
        self.btn_heading2 = QPushButton("H2")
        self.btn_bullet = QPushButton("•")
        self.btn_number = QPushButton("1.")
        self.btn_link = QPushButton("🔗")
        self.btn_image = QPushButton("🖼️")

        self.btn_bold.setToolTip("Жирный текст: **текст**")
        self.btn_italic.setToolTip("Курсив: *текст*")
        self.btn_code.setToolTip("Встроенный код: `код`")
        self.btn_heading1.setToolTip("Заголовок 1 уровня: # Заголовок")
        self.btn_heading2.setToolTip("Заголовок 2 уровня: ## Заголовок")
        self.btn_bullet.setToolTip("Маркированный список")
        self.btn_number.setToolTip("Нумерованный список")
        self.btn_link.setToolTip("Вставить ссылку")
        self.btn_image.setToolTip("Вставить изображение")

        format_container.addWidget(self.btn_bold)
        format_container.addWidget(self.btn_italic)
        format_container.addWidget(self.btn_code)
        format_container.addWidget(self.btn_heading1)
        format_container.addWidget(self.btn_heading2)
        format_container.addWidget(self.btn_bullet)
        format_container.addWidget(self.btn_number)
        format_container.addWidget(self.btn_link)
        format_container.addWidget(self.btn_image)

        save_container = QHBoxLayout()
        save_container.setSpacing(4)
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.setToolTip("Сохранить заметку")
        save_container.addStretch()
        save_container.addWidget(self.btn_save)

        toolbar.addLayout(format_container)
        toolbar.addStretch()
        toolbar.addLayout(save_container)

        self.markdown_editor = MarkdownEditor()
        layout.addLayout(toolbar)
        layout.addWidget(self.markdown_editor)

        self.setup_connections()

    def setup_connections(self):
        self.btn_bold.clicked.connect(self.insert_bold)
        self.btn_italic.clicked.connect(self.insert_italic)
        self.btn_code.clicked.connect(self.insert_code)
        self.btn_link.clicked.connect(self.insert_link)
        self.btn_image.clicked.connect(self.insert_image)
        self.btn_heading1.clicked.connect(self.insert_heading1)
        self.btn_heading2.clicked.connect(self.insert_heading2)
        self.btn_bullet.clicked.connect(self.insert_bullet_list)
        self.btn_number.clicked.connect(self.insert_numbered_list)
        self.btn_save.clicked.connect(self.save_note)

    def insert_bold(self):
        self._wrap_selection("**", "**")

    def insert_italic(self):
        self._wrap_selection("*", "*")

    def insert_code(self):
        self._wrap_selection("`", "`")

    def insert_heading1(self):
        self._insert_at_line_start("# ")

    def insert_heading2(self):
        self._insert_at_line_start("## ")

    def insert_bullet_list(self):
        self._insert_at_line_start("- ")

    def insert_numbered_list(self):
        self._insert_at_line_start("1. ")

    def insert_link(self):
        cursor = self.markdown_editor.editor.textCursor()
        cursor.insertText("[текст ссылки](https://example.com)")

    def insert_image(self):
        cursor = self.markdown_editor.editor.textCursor()
        cursor.insertText("![альтернативный текст](путь/к/изображению.jpg)")

    def save_note(self):
        markdown_content = self.markdown_editor.get_markdown()
        print("Сохранение заметки в БД...")
        if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
            self.parent().status_bar.showMessage("Заметка сохранена", 2000)

    def _wrap_selection(self, before, after):
        editor = self.markdown_editor.editor
        cursor = editor.textCursor()

        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{before}{selected_text}{after}")
        else:
            cursor.insertText(f"{before}текст{after}")
            pos = cursor.position() - len(after) - 4
            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
            editor.setTextCursor(cursor)

    def _insert_at_line_start(self, text):
        editor = self.markdown_editor.editor
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText(text)
        editor.setTextCursor(cursor)