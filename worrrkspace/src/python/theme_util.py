# theme_util.py
"""
Утилита для определения системной темы и применения её к QApplication.
Поддерживает Windows (реестр + PowerShell fallback), macOS, Linux (gnome/kde/env).
Возвращаемые значения: 'dark', 'light' или 'unknown'.
"""

import platform
import subprocess
import shutil
from pathlib import Path
from PyQt6 import QtGui, QtWidgets, QtCore


class SystemThemeDetector:
    """Класс-утилита для определения системной темы."""

    @staticmethod
    def get_system_theme():
        """Определяет системную тему: 'dark' / 'light' / 'unknown'."""
        system = platform.system().lower()
        try:
            if system == "windows":
                return SystemThemeDetector._get_windows_theme()
            elif system == "darwin":
                return SystemThemeDetector._get_macos_theme()
            elif system == "linux":
                return SystemThemeDetector._get_linux_theme()
            else:
                return "unknown"
        except Exception as e:
            print("SystemThemeDetector.get_system_theme error:", e)
            return "unknown"

    # ----------------- Windows -----------------
    @staticmethod
    def _get_windows_theme():
        """Определяет тему в Windows через реестр и, при неудаче, PowerShell."""
        try:
            import winreg
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            # AppsUseLightTheme: 1 = light, 0 = dark
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    # попробуем AppsUseLightTheme, затем SystemUsesLightTheme
                    try:
                        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                        return "light" if int(value) == 1 else "dark"
                    except FileNotFoundError:
                        try:
                            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
                            return "light" if int(value) == 1 else "dark"
                        except Exception:
                            pass
            except FileNotFoundError:
                pass
        except Exception:
            # winreg может не существовать в некоторых окружениях
            pass

        # fallback — попробовать PowerShell (pwsh или powershell)
        try:
            return SystemThemeDetector._get_windows_theme_powershell()
        except Exception:
            return "unknown"

    @staticmethod
    def _get_windows_theme_powershell():
        """PowerShell fallback: пытаемся прочитать реестр через PowerShell."""
        for exe in ("powershell", "pwsh"):
            if shutil.which(exe) is None:
                continue
            try:
                # возвращает 0 или 1 или пустую строку
                ps_cmd = (
                    'Try {'
                    ' $v = Get-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -ErrorAction Stop;'
                    ' $v.AppsUseLightTheme'
                    '} Catch { "" }'
                )
                result = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                                        capture_output=True, text=True, timeout=6)
                out = (result.stdout or "").strip()
                if out != "":
                    try:
                        iv = int(out)
                        return "light" if iv == 1 else "dark"
                    except Exception:
                        pass
            except Exception:
                continue
        return "unknown"

    # ----------------- macOS -----------------
    @staticmethod
    def _get_macos_theme():
        """Определяет тему на macOS через defaults."""
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=6
            )
            if result.returncode == 0:
                out = (result.stdout or "").strip().lower()
                return "dark" if "dark" in out else "light"
            # если команда вернула ненулевой код — обычно означает светлую тему
            return "light"
        except Exception:
            return "unknown"

    # ----------------- Linux -----------------
    @staticmethod
    def _get_linux_theme():
        """Определяет тему в Linux, пробуя GNOME, KDE и переменные окружения."""
        # GNOME via gsettings
        try:
            if shutil.which("gsettings"):
                r = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0:
                    theme_name = (r.stdout or "").strip().lower().strip("'\"")
                    if "dark" in theme_name:
                        return "dark"
                    else:
                        return "light"
        except Exception:
            pass

        # dconf fallback
        try:
            if shutil.which("dconf"):
                r = subprocess.run(
                    ["dconf", "read", "/org/gnome/desktop/interface/gtk-theme"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0:
                    theme_name = (r.stdout or "").strip().lower().strip("'\"")
                    if "dark" in theme_name:
                        return "dark"
                    else:
                        return "light"
        except Exception:
            pass

        # KDE - check kdeglobals
        try:
            cfg = Path.home() / ".config" / "kdeglobals"
            if cfg.exists():
                data = cfg.read_text(encoding="utf-8", errors="ignore").lower()
                if "color=dark" in data or "dark" in data:
                    return "dark"
                else:
                    return "light"
        except Exception:
            pass

        # Environment variables
        try:
            env = QtCore.QProcessEnvironment.systemEnvironment()
            for var in ("GTK_THEME", "DESKTOP_THEME", "CURRENT_THEME", "XDG_CURRENT_DESKTOP"):
                val = env.value(var, "").lower()
                if "dark" in val:
                    return "dark"
                elif "light" in val and val != "":
                    return "light"
        except Exception:
            pass

        return "unknown"

    # ----------------- Colors & Apply -----------------
    @staticmethod
    def get_system_colors(theme=None):
        """Возвращает словарь базовых цветов для темы."""
        if theme is None:
            theme = SystemThemeDetector.get_system_theme()

        if theme == "dark":
            return {
                "window": "#0b1220",
                "window_text": "#e6eef8",
                "base": "#14181c",
                "alternate_base": "#1e262b",
                "text": "#e6eef8",
                "button": "#2a7de1",
                "button_text": "#ffffff",
                "highlight": "#2a82da",
                "highlighted_text": "#ffffff",
                "tooltip_base": "#2d2d30",
                "tooltip_text": "#ffffff",
                "label_text": "#e6eef8",
            }
        else:
            return {
                "window": "#f7fbff",
                "window_text": "#07203a",
                "base": "#ffffff",
                "alternate_base": "#f5f9fc",
                "text": "#07203a",
                "button": "#2a82da",
                "button_text": "#ffffff",
                "highlight": "#0078d4",
                "highlighted_text": "#ffffff",
                "tooltip_base": "#ffffe1",
                "tooltip_text": "#000000",
                "label_text": "#07203a",
            }

    @staticmethod
    def apply_system_theme(app, theme=None):
        """
        Применяет палитру и базовые stylesheet к QApplication.
        При ошибке — подаёт стиль через setStyleSheet из ThemeManager.
        """
        if app is None:
            app = QtWidgets.QApplication.instance()
            if app is None:
                raise RuntimeError("QApplication instance not found")

        theme = theme or SystemThemeDetector.get_system_theme()
        colors = SystemThemeDetector.get_system_colors(theme)

        palette = QtGui.QPalette()

        # Устанавливаем основные роли
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(colors["window"]))
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(colors["window_text"]))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(colors["base"]))
        palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(colors["alternate_base"]))
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(colors["text"]))
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(colors["button"]))
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(colors["button_text"]))
        palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(colors["highlight"]))
        palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(colors["highlighted_text"]))
        palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(colors["tooltip_base"]))
        palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(colors["tooltip_text"]))

        # WindowText для QLabel (обеспечивает корректный контраст)
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(colors["label_text"]))

        # Disabled states (PyQt6: используем ColorGroup enum)
        try:
            palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text,
                             QtGui.QColor(colors["text"]).darker(140))
            palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText,
                             QtGui.QColor(colors["button_text"]).darker(140))
            palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.WindowText,
                             QtGui.QColor(colors["label_text"]).darker(140))
        except Exception:
            # В редком случае используем старый API
            pass

        app.setPalette(palette)

        # Применяем полные стили
        if theme == "dark":
            SystemThemeDetector._apply_dark_stylesheet(app)
        else:
            SystemThemeDetector._apply_light_stylesheet(app)

    @staticmethod
    def _apply_dark_stylesheet(app):
        stylesheet = """
        /* Основные стили */
        QMainWindow, QWidget, QDialog {
            background-color: #0b1220;
            color: #e6eef8;
        }

        /* Верхняя панель и меню */
        QToolBar {
            background-color: #14181c;
            border-bottom: 1px solid #2b2f33;
            spacing: 5px;
            padding: 5px;
        }

        QToolButton {
            background: transparent;
            color: #e6eef8;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 12px;
        }

        QToolButton:hover {
            background: rgba(255,255,255,0.1);
        }

        /* Комбобокс */
        QComboBox {
            background-color: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            border-radius: 6px;
            padding: 6px 10px;
            min-width: 120px;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #e6eef8;
        }

        QComboBox QAbstractItemView {
            background-color: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            selection-background-color: #2a82da;
        }

        /* Вкладки */
        QTabWidget::pane {
            border: 1px solid #2b2f33;
            background: #14181c;
            top: -1px;
        }

        QTabBar::tab {
            background: #1e2328;
            color: #e6eef8;
            padding: 8px 12px;
            margin-right: 1px;
            border: none;
            border-bottom: 2px solid transparent;
        }

        QTabBar::tab:selected {
            background: #0b1220;
            color: #e6eef8;
            border-bottom: 2px solid #2a82da;
        }

        QTabBar::tab:hover {
            background: #2a2f35;
        }

        /* Статус бар */
        QStatusBar {
            background: #14181c;
            color: #e6eef8;
            border-top: 1px solid #2b2f33;
        }

        /* Кнопки */
        QPushButton {
            background-color: #2a7de1;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2469ba;
        }

        QPushButton:pressed {
            background-color: #1d55a0;
        }

        /* Поля ввода */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #2a82da;
        }

        /* Док-виджеты */
        QDockWidget {
            background: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }

        QDockWidget::title {
            background: #1e2328;
            color: #e6eef8;
            padding: 6px;
            text-align: center;
        }

        QDockWidget::close-button, QDockWidget::float-button {
            background: transparent;
            color: #e6eef8;
            border: none;
            padding: 2px;
        }

        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background: rgba(255,255,255,0.1);
        }

        /* Дерево */
        QTreeWidget {
            background-color: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            border-radius: 6px;
            outline: 0;
        }

        QTreeWidget::item {
            padding: 4px;
            border: 1px solid transparent;
        }

        QTreeWidget::item:selected {
            background-color: #2a82da;
            color: white;
        }

        QTreeWidget::item:hover {
            background: rgba(255,255,255,0.1);
        }

        /* Заголовки дерева (QHeaderView) */
        QHeaderView {
            background-color: #1e2328;
            color: #e6eef8;
            border: none;
        }

        QHeaderView::section {
            background-color: #1e2328;
            color: #e6eef8;
            border: 1px solid #2b2f33;
            padding: 5px;
            font-weight: bold;
        }

        QHeaderView::section:checked {
            background-color: #2a82da;
        }

        QHeaderView::section:hover {
            background-color: #2a2f35;
        }

        /* Чекбокс */
        QCheckBox {
            background: transparent;
            color: #e6eef8;
            spacing: 5px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #2b2f33;
            border-radius: 3px;
            background: #14181c;
        }

        QCheckBox::indicator:checked {
            background: #2a82da;
            border: 1px solid #2a82da;
        }

        QCheckBox::indicator:hover {
            border: 1px solid #2a82da;
        }

        /* Фреймы */
        QFrame {
            background: transparent;
            color: #e6eef8;
        }

        QFrame[frameShape="4"], QFrame[frameShape="5"] {
            /* StyledPanel и Raised */
            background: #1e2328;
            border: 1px solid #2b2f33;
            border-radius: 8px;
        }

        /* Меню */
        QMenu {
            background-color: #14181c;
            color: #e6eef8;
            border: 1px solid #2b2f33;
        }

        QMenu::item {
            padding: 5px 20px 5px 20px;
        }

        QMenu::item:selected {
            background-color: #2a82da;
        }

        QMenu::separator {
            height: 1px;
            background: #2b2f33;
        }

        /* Label */
        QLabel {
            background: transparent;
            color: #e6eef8;
        }

        /* Scroll bars */
        QScrollBar:vertical {
            background: #14181c;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #2b2f33;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #3a3f45;
        }

        QScrollBar:horizontal {
            background: #14181c;
            height: 12px;
            margin: 0px;
        }

        QScrollBar::handle:horizontal {
            background: #2b2f33;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #3a3f45;
        }

        QTableWidget > QTableCornerButton::section {
            background-color: #1e2328;
            border: 1px solid #1e2328;
            border-right: 1px solid #1e2328;
            border-bottom: 1px solid #1e2328;
        }


        QTableCornerButton::section {
            background-color: #1e2328;
            border-top: 1px solid #1e2328;
            border-left: 1px solid #1e2328;
            border-right: 1px solid #1e2328;
            border-bottom: 1px solid #1e2328;
        }
        """
        app.setStyleSheet(stylesheet)

    @staticmethod
    def _apply_light_stylesheet(app):
        stylesheet = """
        /* Основные стили */
        QMainWindow, QWidget, QDialog {
            background-color: #f7fbff;
            color: #07203a;
        }

        /* Верхняя панель и меню */
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #d7dde6;
            spacing: 5px;
            padding: 5px;
        }

        QToolButton {
            background: transparent;
            color: #07203a;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 12px;
        }

        QToolButton:hover {
            background: rgba(0,0,0,0.05);
        }

        /* Комбобокс */
        QComboBox {
            background-color: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
            border-radius: 6px;
            padding: 6px 10px;
            min-width: 120px;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #07203a;
        }

        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
            selection-background-color: #2a82da;
        }

        /* Вкладки */
        QTabWidget::pane {
            border: 1px solid #d7dde6;
            background: #fafafa;
            top: -1px;
        }

        QTabBar::tab {
            background: #f0f0f0;
            color: #666666;
            padding: 8px 12px;
            margin-right: 1px;
            border: none;
            border-bottom: 2px solid transparent;
        }

        QTabBar::tab:selected {
            background: white;
            color: #333333;
            border-bottom: 2px solid #2a82da;
        }

        QTabBar::tab:hover {
            background: #e8e8e8;
        }

        /* Статус бар */
        QStatusBar {
            background: #ffffff;
            color: #07203a;
            border-top: 1px solid #d7dde6;
        }

        /* Кнопки */
        QPushButton {
            background-color: #2a82da;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #1f63a8;
        }

        QPushButton:pressed {
            background-color: #1a5490;
        }

        /* Поля ввода */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #2a82da;
        }

        /* Док-виджеты */
        QDockWidget {
            background: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }

        QDockWidget::title {
            background: #f0f0f0;
            color: #07203a;
            padding: 6px;
            text-align: center;
        }

        QDockWidget::close-button, QDockWidget::float-button {
            background: transparent;
            color: #07203a;
            border: none;
            padding: 2px;
        }

        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background: rgba(0,0,0,0.1);
        }

        /* Дерево */
        QTreeWidget {
            background-color: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
            border-radius: 6px;
            outline: 0;
        }

        QTreeWidget::item {
            padding: 4px;
            border: 1px solid transparent;
        }

        QTreeWidget::item:selected {
            background-color: #2a82da;
            color: white;
        }

        QTreeWidget::item:hover {
            background: rgba(0,0,0,0.05);
        }

        /* Заголовки дерева (QHeaderView) */
        QHeaderView {
            background-color: #f0f0f0;
            color: #07203a;
            border: none;
        }

        QHeaderView::section {
            background-color: #f0f0f0;
            color: #07203a;
            border: 1px solid #d7dde6;
            padding: 5px;
            font-weight: bold;
        }

        QHeaderView::section:checked {
            background-color: #2a82da;
            color: white;
        }

        QHeaderView::section:hover {
            background-color: #e8e8e8;
        }

        /* Чекбокс */
        QCheckBox {
            background: transparent;
            color: #07203a;
            spacing: 5px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #d7dde6;
            border-radius: 3px;
            background: #ffffff;
        }

        QCheckBox::indicator:checked {
            background: #2a82da;
            border: 1px solid #2a82da;
        }

        QCheckBox::indicator:hover {
            border: 1px solid #2a82da;
        }

        /* Фреймы */
        QFrame {
            background: transparent;
            color: #07203a;
        }

        QFrame[frameShape="4"], QFrame[frameShape="5"] {
            /* StyledPanel и Raised */
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }

        /* Меню */
        QMenu {
            background-color: #ffffff;
            color: #07203a;
            border: 1px solid #d7dde6;
        }

        QMenu::item {
            padding: 5px 20px 5px 20px;
        }

        QMenu::item:selected {
            background-color: #2a82da;
            color: white;
        }

        QMenu::separator {
            height: 1px;
            background: #d7dde6;
        }

        /* Label */
        QLabel {
            background: transparent;
            color: #07203a;
        }

        /* Scroll bars */
        QScrollBar:vertical {
            background: #f0f0f0;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #a0a0a0;
        }

        QScrollBar:horizontal {
            background: #f0f0f0;
            height: 12px;
            margin: 0px;
        }

        QScrollBar::handle:horizontal {
            background: #c0c0c0;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #a0a0a0;
        }
        
        QTableCornerButton::section {
            background: #f0f0f0;
            border: 1px solid #d7dde6;
        }
        """
        app.setStyleSheet(stylesheet)