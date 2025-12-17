# theme_manager.py
import os
import sys
from PyQt6.QtCore import QSettings

# Попытки гибкого импорта SystemThemeDetector из возможных мест
def _import_system_theme_detector():
    candidates = [
        "utils.python.theme_util",
        "utils.python.theme_utils",
        "theme_util",
        "theme_utils",
    ]
    for mod in candidates:
        try:
            __import__(mod)
            module = sys.modules[mod]
            if hasattr(module, "SystemThemeDetector"):
                return getattr(module, "SystemThemeDetector")
        except Exception:
            continue
    # fallback: попробуем добавить текущую папку (если модуль лежит рядом)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    for mod in ["theme_util", "theme_utils"]:
        try:
            __import__(mod)
            module = sys.modules[mod]
            if hasattr(module, "SystemThemeDetector"):
                return getattr(module, "SystemThemeDetector")
        except Exception:
            continue
    raise ImportError("Не удалось импортировать SystemThemeDetector из известных мест.")


SystemThemeDetector = _import_system_theme_detector()


class ThemeManager:
    """Менеджер тем для приложения."""

    def __init__(self, organization="YourCompany", application="YourApp"):
        self.settings = QSettings(organization, application)
        self.current_theme = self.load_theme()

    def load_theme(self):
        """Загружает сохранённую тему (если есть) или определяет системную."""
        saved_theme = self.settings.value("theme", "")
        if isinstance(saved_theme, str) and saved_theme.lower() in ("dark", "light"):
            return saved_theme.lower()
        # если не задана — опрашиваем систему
        system_theme = SystemThemeDetector.get_system_theme()
        if system_theme in ("dark", "light"):
            return system_theme
        # по-умолчанию светлая
        return "light"

    def save_theme(self, theme):
        """Сохраняет выбранную тему."""
        theme = (theme or "").lower()
        if theme not in ("dark", "light"):
            raise ValueError("theme must be 'dark' or 'light'")
        self.settings.setValue("theme", theme)
        self.current_theme = theme

    def toggle_theme(self):
        """Переключает тему и возвращает новую тему."""
        new = "light" if self.current_theme == "dark" else "dark"
        self.save_theme(new)
        return self.current_theme

    def get_theme_stylesheet(self, theme=None):
        """Возвращает стили для указанной темы (строка)."""
        if theme is None:
            theme = self.current_theme

        theme = theme.lower()
        if theme == "dark":
            return (
                "QWidget {"
                " background-color: #0b1220;"
                " color: #e6eef8;"
                " }"
                "QLabel { background: transparent; color: #e6eef8; }"
                "QLineEdit { background-color: #14181c; color: #e6eef8; border: 1px solid #2b2f33; border-radius: 6px; padding: 6px; }"
                "QPushButton { background-color: #2a7de1; color: #ffffff; border: none; border-radius: 6px; padding: 8px 14px; }"
                "QPushButton:hover { background-color: #2469ba; }"
                "QCheckBox { background: transparent; color: #e6eef8; }"
            )
        else:
            return (
                "QWidget {"
                " background-color: #f7fbff;"
                " color: #07203a;"
                " }"
                "QLabel { background: transparent; color: #07203a; }"
                "QLineEdit { background-color: #ffffff; color: #07203a; border: 1px solid #d7dde6; border-radius: 6px; padding: 6px; }"
                "QPushButton { background-color: #2a82da; color: #ffffff; border: none; border-radius: 6px; padding: 8px 14px; }"
                "QPushButton:hover { background-color: #1f63a8; }"
                "QCheckBox { background: transparent; color: #07203a; }"
            )


# Тестовый запуск и хелп функции для применения темы к QApplication
def setup_app_theme(app=None, theme=None):
    """
    Применяет тему к приложению.
    Если app не передан, используется текущий QApplication.instance()
    """
    from PyQt6 import QtWidgets

    if app is None:
        app = QtWidgets.QApplication.instance()
    if app is None:
        raise RuntimeError("Нет активного QApplication. Передайте объект app.")

    # Если пользователь явно передал тему, применим её,
    # иначе попытаемся прочитать сохранённую или системную.
    tm = ThemeManager()
    if theme is None:
        theme_to_apply = tm.current_theme
    else:
        theme_to_apply = theme.lower() if isinstance(theme, str) else tm.current_theme

    # Применяем палитру и стили через SystemThemeDetector (если есть)
    try:
        SystemThemeDetector.apply_system_theme(app, theme=theme_to_apply)
    except Exception:
        # fallback: применяем просто stylesheet из менеджера
        stylesheet = tm.get_theme_stylesheet(theme=theme_to_apply)
        app.setStyleSheet(stylesheet)

    return theme_to_apply


if __name__ == "__main__":
    # Небольшой демонстрационный тест (если запустить файл отдельно)
    try:
        from PyQt6 import QtWidgets
        import sys

        app = QtWidgets.QApplication(sys.argv)
        applied = setup_app_theme(app)
        print("Applied theme:", applied)

        w = QtWidgets.QMainWindow()
        w.setWindowTitle(f"ThemeManager test ({applied})")
        w.setGeometry(200, 200, 480, 320)
        cw = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(cw)
        layout.addWidget(QtWidgets.QLabel(f"Current theme: {applied}"))
        layout.addWidget(QtWidgets.QPushButton("Sample Button"))
        layout.addWidget(QtWidgets.QLineEdit("Sample input"))
        w.setCentralWidget(cw)
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Ошибка при тестировании ThemeManager:", e)
