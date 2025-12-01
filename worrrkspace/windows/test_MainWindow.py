"""WoRRRkspace MainWindow с PyTablerIcons и работающими виджетами"""

import sys
import os
import warnings
from pathlib import Path
from typing import Dict, Tuple

warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*sipPyTypeDict.*")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QPoint, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QToolButton, QTabWidget, QStatusBar,
    QMenu, QPushButton, QTextEdit, QLineEdit, QSplitter,
    QListWidget, QListWidgetItem, QDockWidget, QDialog
)
from PyQt6.QtGui import QIcon, QAction

# =============================================================================
# ПРОВЕРКА И ИМПОРТ PyTablerIcons
# =============================================================================

try:
    from pytablericons import TablerIcons, OutlineIcon, FilledIcon
    PYTABLERICONS_AVAILABLE = True
    print("✅ PyTablerIcons imported successfully!")
except ImportError as e:
    print(f"❌ PyTablerIcons import error: {e}")
    PYTABLERICONS_AVAILABLE = False

# =============================================================================
# ICON MANAGER ДЛЯ PyTablerIcons
# =============================================================================

class IconManager:
    """Менеджер иконок с использованием PyTablerIcons"""
    
    # Кэш для иконок: (icon_name, size, color) -> QIcon
    _icon_cache: Dict[Tuple[str, int, str], QIcon] = {}
    
    # Маппинг иконок для нашего приложения
    ICON_MAP = {
        # Основные иконки
        "theme_light": "SUN",
        "theme_dark": "MOON",
        "profile": "USER_CIRCLE",
        "menu": "MENU_2",
        "workspace": "LAYOUT_DASHBOARD",
        
        # Иконки для ToolsPanel
        "table": "TABLE",
        "note": "NOTE",
        "graph": "CHART_ARCS_3",
        "task": "CHECKLIST",
        "save": "DEVICE_FLOPPY",
        "settings": "SETTINGS",
        
        # Иконки для панелей
        "solution_explorer": "FOLDERS",
        "tools": "TOOLS",
        "chat": "MESSAGE_CHATBOT",
        "logs": "TERMINAL_2",
        
        # Общие иконки
        "add": "PLUS",
        "delete": "TRASH",
        "edit": "EDIT",
        "close": "X",
        "refresh": "REFRESH"
    }
    
    @classmethod
    def get_icon(cls, icon_key: str, size: int = 24, color: str = "#000000") -> QIcon:
        """
        Получить иконку из PyTablerIcons
        
        Args:
            icon_key: Ключ иконки из ICON_MAP
            size: Размер иконки в пикселях
            color: Цвет в формате HEX (#RRGGBB)
        
        Returns:
            QIcon объект или пустая иконка при ошибке
        """
        if not PYTABLERICONS_AVAILABLE:
            return QIcon()
        
        cache_key = (icon_key, size, color)
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]
        
        try:
            # Получаем имя иконки из маппинга
            icon_name = cls.ICON_MAP.get(icon_key)
            if not icon_name:
                print(f"⚠️ Icon key '{icon_key}' not found in ICON_MAP")
                return QIcon()
            
            # Пытаемся загрузить иконку
            try:
                icon_obj = TablerIcons.load(
                    getattr(OutlineIcon, icon_name),
                    size=size,
                    color=color
                )
                qicon = QIcon(icon_obj.toqpixmap())
                cls._icon_cache[cache_key] = qicon
                return qicon
            except AttributeError:
                print(f"⚠️ Icon '{icon_name}' not found in PyTablerIcons")
                return QIcon()
                
        except Exception as e:
            print(f"❌ Error loading icon {icon_key}: {e}")
            return QIcon()
    
    @classmethod
    def get_theme_icon(cls, theme: str = "light", size: int = 24) -> QIcon:
        """Получить иконку для переключения темы"""
        icon_key = "theme_dark" if theme == "light" else "theme_light"
        color = "#FFFFFF" if theme == "dark" else "#000000"
        return cls.get_icon(icon_key, size, color)
    
    @classmethod
    def get_tools_icon(cls, tool_type: str, size: int = 20, theme: str = "light") -> QIcon:
        """Получить иконку для инструментов"""
        color = "#FFFFFF" if theme == "dark" else "#000000"
        return cls.get_icon(tool_type, size, color)
    
    @classmethod
    def clear_cache(cls):
        """Очистить кэш иконок"""
        cls._icon_cache.clear()

# =============================================================================
# ИМПОРТ ВИДЖЕТОВ
# =============================================================================

# Добавляем пути импорта
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
worrrkspace_path = project_root / "worrrkspace"

sys.path.insert(0, str(worrrkspace_path / "ui" / "widgets"))
sys.path.insert(0, str(worrrkspace_path / "ui" / "panels"))
sys.path.insert(0, str(worrrkspace_path / "src" / "python"))

try:
    from theme_util import SystemThemeDetector
    from theme_manager import setup_app_theme, ThemeManager
    print("✅ Импортированы theme модули")
except ImportError:
    print("⚠️ Использую fallback для theme модулей")
    
    class SystemThemeDetector:
        def get_system_theme(self):
            return "light"
    
    class ThemeManager:
        def __init__(self, organization, application):
            self.current_theme = "light"
        
        def toggle_theme(self):
            self.current_theme = "dark" if self.current_theme == "light" else "light"
            return self.current_theme
    
    def setup_app_theme(app, theme="light"):
        app.setStyle("Fusion")

# Импорт виджетов с fallback
try:
    from base_widgets import ProfileDialog
    print("✅ Импортирован ProfileDialog")
except ImportError as e:
    print(f"⚠️ Ошибка импорта ProfileDialog: {e}")
    
    class ProfileDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Профиль")
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Профиль пользователя"))
            btn = QPushButton("Закрыть")
            btn.clicked.connect(self.accept)
            layout.addWidget(btn)
            self.setLayout(layout)

try:
    from markdown_editor import MarkdownNoteTab
    print("✅ Импортирован MarkdownNoteTab")
except ImportError as e:
    print(f"⚠️ Ошибка импорта MarkdownNoteTab: {e}")
    
    class MarkdownNoteTab(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            self.text_edit = QTextEdit()
            self.text_edit.setPlaceholderText("Введите Markdown текст...")
            layout.addWidget(self.text_edit)
            self.setLayout(layout)

try:
    from table_editor import TableEditorTab
    print("✅ Импортирован TableEditorTab")
except ImportError as e:
    print(f"⚠️ Ошибка импорта TableEditorTab: {e}")
    
    class TableEditorTab(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            from PyQt6.QtWidgets import QTableWidget
            layout = QVBoxLayout()
            self.table = QTableWidget(5, 5)
            layout.addWidget(self.table)
            self.setLayout(layout)

try:
    from graph_editor import GraphTab
    print("✅ Импортирован GraphTab")
except ImportError as e:
    print(f"⚠️ Ошибка импорта GraphTab: {e}")
    
    class GraphTab(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Редактор графов"))
            layout.addWidget(QLabel("(Используйте оригинальный graph_editor.py для полной функциональности)"))
            self.setLayout(layout)

try:
    from task_editor import TaskTab
    print("✅ Импортирован TaskTab")
except ImportError as e:
    print(f"⚠️ Ошибка импорта TaskTab: {e}")
    
    class TaskTab(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Редактор задач"))
            self.setLayout(layout)

# Импорт панелей с fallback
try:
    from solution_explorer import SolutionExplorer
    print("✅ Импортирован SolutionExplorer")
except ImportError as e:
    print(f"⚠️ Ошибка импорта SolutionExplorer: {e}")
    
    class SolutionExplorer(QDockWidget):
        def __init__(self, parent=None):
            super().__init__("Solution Explorer", parent)
            widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Solution Explorer"))
            widget.setLayout(layout)
            self.setWidget(widget)

try:
    from tools_panel import ToolsPanel
    print("✅ Импортирован ToolsPanel")
except ImportError as e:
    print(f"⚠️ Ошибка импорта ToolsPanel: {e}")
    
    class ToolsPanel(QDockWidget):
        def __init__(self, parent=None):
            super().__init__("Tools", parent)
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Создаем кнопки как в работающей версии
            self.btn_table = QPushButton()
            self.btn_note = QPushButton()
            self.btn_graph = QPushButton()
            self.btn_task = QPushButton()
            
            # Устанавливаем текст
            self.btn_table.setText("Таблица")
            self.btn_note.setText("Заметка")
            self.btn_graph.setText("Граф")
            self.btn_task.setText("Задача")
            
            # Настраиваем размер
            for btn in [self.btn_table, self.btn_note, self.btn_graph, self.btn_task]:
                btn.setMinimumHeight(40)
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
            
            layout.addWidget(self.btn_table)
            layout.addWidget(self.btn_note)
            layout.addWidget(self.btn_graph)
            layout.addWidget(self.btn_task)
            layout.addStretch()
            
            widget.setLayout(layout)
            self.setWidget(widget)

try:
    from chat_panel import ChatPanel
    print("✅ Импортирован ChatPanel")
except ImportError as e:
    print(f"⚠️ Ошибка импорта ChatPanel: {e}")
    
    class ChatPanel(QDockWidget):
        def __init__(self, parent=None):
            super().__init__("Chat", parent)
            widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Чат"))
            widget.setLayout(layout)
            self.setWidget(widget)

try:
    from logs_panel import LogsPanel
    print("✅ Импортирован LogsPanel")
except ImportError as e:
    print(f"⚠️ Ошибка импорта LogsPanel: {e}")
    
    class LogsPanel(QDockWidget):
        def __init__(self, parent=None):
            super().__init__("Logs", parent)
            widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Логи"))
            widget.setLayout(layout)
            self.setWidget(widget)

# =============================================================================
# TOP BAR С PYTABLERICONS
# =============================================================================

class TopBar(QWidget):
    workspace_changed = pyqtSignal(str)
    profile_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()

    def __init__(self, parent=None, theme="light"):
        super().__init__(parent)
        self._theme = theme
        self.setFixedHeight(56)
        self.setup_ui()
        self.update_icons()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(8)

        # Кнопка темы с иконкой PyTablerIcons
        self.theme_button = QToolButton()
        self.theme_button.setToolTip("Переключить тему")
        self.theme_button.setAutoRaise(True)
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)
        self.theme_button.setFixedSize(40, 40)
        self.theme_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.theme_button)

        layout.addStretch()

        # Выбор workspace
        self.workspace_combo = QComboBox()
        self.workspace_combo.setMinimumWidth(260)
        self.workspace_combo.addItems(["По умолчанию", "Разработка", "Аналитика", "Пользовательское"])
        self.workspace_combo.setToolTip("Выберите рабочее пространство")
        
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.workspace_combo)
        center_layout.addStretch()
        
        layout.addWidget(center_widget)
        layout.addStretch()

        # Кнопки профиля и меню панелей с PyTablerIcons
        self.profile_button = QToolButton()
        self.profile_button.setToolTip("Открыть профиль")
        self.profile_button.setAutoRaise(True)
        self.profile_button.setFixedSize(40, 40)
        self.profile_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)

        self.panel_menu_button = QToolButton()
        self.panel_menu_button.setToolTip("Показать/скрыть панели")
        self.panel_menu_button.setAutoRaise(True)
        self.panel_menu_button.setFixedSize(40, 40)
        self.panel_menu_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)

        self.panel_menu = QMenu(self)

        def _show_panel_menu():
            if self.panel_menu_button:
                pos = self.panel_menu_button.mapToGlobal(QPoint(0, self.panel_menu_button.height()))
                if self.panel_menu.actions():
                    self.panel_menu.exec(pos)

        self.panel_menu_button.clicked.connect(_show_panel_menu)

        layout.addWidget(self.profile_button)
        layout.addWidget(self.panel_menu_button)

        self.workspace_combo.currentTextChanged.connect(self.workspace_changed.emit)

    def update_icons(self):
        """Обновить иконки в соответствии с текущей темой"""
        # Цвет иконок в зависимости от темы
        icon_color = "#FFFFFF" if self._theme == "dark" else "#000000"
        
        # Иконка темы (свет/луна)
        theme_icon = IconManager.get_theme_icon(self._theme, 24)
        if not theme_icon.isNull():
            self.theme_button.setIcon(theme_icon)
        
        # Иконка профиля
        profile_icon = IconManager.get_icon("profile", 24, icon_color)
        if not profile_icon.isNull():
            self.profile_button.setIcon(profile_icon)
        
        # Иконка меню
        menu_icon = IconManager.get_icon("menu", 24, icon_color)
        if not menu_icon.isNull():
            self.panel_menu_button.setIcon(menu_icon)

    def update_theme(self, theme: str):
        """Обновить тему и иконки"""
        self._theme = theme
        self.update_icons()
        
        # Обновляем стиль кнопок для темной темы
        if theme == "dark":
            button_style = """
                QToolButton {
                    border: 1px solid #555;
                    border-radius: 6px;
                }
                QToolButton:hover {
                    background-color: #444;
                }
            """
        else:
            button_style = """
                QToolButton {
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }
                QToolButton:hover {
                    background-color: #f0f0f0;
                }
            """
        
        for btn in [self.theme_button, self.profile_button, self.panel_menu_button]:
            btn.setStyleSheet(button_style)

    def set_panels_menu(self, actions):
        """Установить меню для панелей"""
        self.panel_menu.clear()
        for act in actions:
            self.panel_menu.addAction(act)

# =============================================================================
# ГЛАВНОЕ ОКНО
# =============================================================================

class MainWindow(QMainWindow):
    WORKSPACE_SETTINGS_KEY = "app/worrrkspace"

    def __init__(self):
        super().__init__()
        self.settings = QSettings("worrrkspace_company", "worrrkspace_app")
        self.theme_manager = ThemeManager(organization="worrrkspace_company", application="worrrkspace_app")
        self.current_theme = self.theme_manager.current_theme
        self.dock_widgets = {}
        self._panel_actions = {}
        
        self._initialize_window()

    def _initialize_window(self):
        self.setWindowTitle("WoRRRkspace")
        self.setMinimumSize(1000, 700)
        self.resize(1400, 900)
        self._center_on_screen()
        
        self._load_ui()
        self._setup_ui()
        self.apply_theme()
        self._setup_connections()
        
        print("🚀 WoRRRkspace успешно инициализирован!")

    def _center_on_screen(self):
        screen = self.screen()
        if screen:
            geom = screen.geometry()
            self.move(geom.center() - self.rect().center())

    def _load_ui(self):
        ui_file = Path(__file__).parent / "MainWindow.ui"
        
        if ui_file.exists():
            try:
                uic.loadUi(ui_file, self)
                print("✅ Загружен UI из MainWindow.ui")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки UI: {e}")
                self._setup_fallback_ui()
        else:
            self._setup_fallback_ui()

    def _setup_fallback_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setTabsClosable(True)
        layout.addWidget(self.main_tab_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_ui(self):
        # Создаем верхнюю панель
        self.top_bar = TopBar(theme=self.current_theme)
        self.setMenuWidget(self.top_bar)
        
        # Подключаем сигналы
        self.top_bar.profile_button.clicked.connect(self.open_profile)
        
        # Создаем панели
        self._create_panels()
        
        # Создаем статус бар если его нет
        if not hasattr(self, "status_bar") or self.statusBar() is None:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
        
        # Загружаем сохраненный workspace
        saved_ws = self.settings.value(self.WORKSPACE_SETTINGS_KEY, "")
        if saved_ws:
            idx = self.top_bar.workspace_combo.findText(saved_ws)
            if idx >= 0:
                self.top_bar.workspace_combo.setCurrentIndex(idx)
        
        # Создаем меню для панелей
        self.rebuild_panel_actions_menu()
        
        # Обновляем иконки для ToolsPanel если нужно
        self._update_tools_panel_icons()

    def _create_panels(self):
        """Создает все панели"""
        try:
            self.solution_explorer = SolutionExplorer(self)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.solution_explorer)
            self.dock_widgets["solution_explorer"] = self.solution_explorer
            print("✅ Создана панель SolutionExplorer")
        except Exception as e:
            print(f"⚠️ Ошибка создания SolutionExplorer: {e}")

        try:
            self.tools_panel = ToolsPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tools_panel)
            self.dock_widgets["tools"] = self.tools_panel
            print("✅ Создана панель ToolsPanel")
        except Exception as e:
            print(f"⚠️ Ошибка создания ToolsPanel: {e}")

        try:
            self.chat_panel = ChatPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chat_panel)
            self.dock_widgets["chat"] = self.chat_panel
            print("✅ Создана панель ChatPanel")
        except Exception as e:
            print(f"⚠️ Ошибка создания ChatPanel: {e}")

        try:
            self.logs_panel = LogsPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.logs_panel)
            self.dock_widgets["logs"] = self.logs_panel
            print("✅ Создана панель LogsPanel")
        except Exception as e:
            print(f"⚠️ Ошибка создания LogsPanel: {e}")
        
        # Пытаемся сгруппировать панели
        try:
            if "solution_explorer" in self.dock_widgets and "tools" in self.dock_widgets:
                self.tabifyDockWidget(
                    self.dock_widgets["solution_explorer"], 
                    self.dock_widgets["tools"]
                )
                self.dock_widgets["solution_explorer"].raise_()
        except Exception as e:
            print(f"⚠️ Ошибка группировки панелей: {e}")

    def _update_tools_panel_icons(self):
        """Обновить иконки в ToolsPanel"""
        if hasattr(self, 'tools_panel'):
            icon_color = "#FFFFFF" if self.current_theme == "dark" else "#000000"
            
            # Обновляем иконки кнопок если они есть
            if hasattr(self.tools_panel, 'btn_table'):
                icon = IconManager.get_icon("table", 20, icon_color)
                if not icon.isNull():
                    self.tools_panel.btn_table.setIcon(icon)
            
            if hasattr(self.tools_panel, 'btn_note'):
                icon = IconManager.get_icon("note", 20, icon_color)
                if not icon.isNull():
                    self.tools_panel.btn_note.setIcon(icon)
            
            if hasattr(self.tools_panel, 'btn_graph'):
                icon = IconManager.get_icon("graph", 20, icon_color)
                if not icon.isNull():
                    self.tools_panel.btn_graph.setIcon(icon)
            
            if hasattr(self.tools_panel, 'btn_task'):
                icon = IconManager.get_icon("task", 20, icon_color)
                if not icon.isNull():
                    self.tools_panel.btn_task.setIcon(icon)

    def _setup_connections(self):
        """Подключает все сигналы"""
        # Подключаем верхнюю панель
        self.top_bar.workspace_changed.connect(self.on_workspace_changed)
        self.top_bar.theme_toggle_requested.connect(self.toggle_theme)
        
        # ПОДКЛЮЧАЕМ КНОПКИ TOOLSPANEL - ВАЖНО!
        if hasattr(self, 'tools_panel'):
            if hasattr(self.tools_panel, 'btn_table'):
                self.tools_panel.btn_table.clicked.connect(lambda: self._open_placeholder_tab("Таблица"))
                print("✅ Подключена кнопка Таблица")
            
            if hasattr(self.tools_panel, 'btn_note'):
                self.tools_panel.btn_note.clicked.connect(lambda: self._open_placeholder_tab("Заметка"))
                print("✅ Подключена кнопка Заметка")
            
            if hasattr(self.tools_panel, 'btn_graph'):
                self.tools_panel.btn_graph.clicked.connect(lambda: self._open_placeholder_tab("Граф"))
                print("✅ Подключена кнопка Граф")
            
            if hasattr(self.tools_panel, 'btn_task'):
                self.tools_panel.btn_task.clicked.connect(lambda: self._open_placeholder_tab("Задача"))
                print("✅ Подключена кнопка Задача")
        
        # Подключаем закрытие вкладок
        if hasattr(self, "main_tab_widget"):
            self.main_tab_widget.tabCloseRequested.connect(self.close_tab)

    def _open_placeholder_tab(self, title: str):
        """Создает вкладку - ТОЧНО КАК В РАБОТАЮЩЕЙ ВЕРСИИ"""
        if not hasattr(self, "main_tab_widget"):
            return

        try:
            if title == "Заметка":
                w = MarkdownNoteTab()
                if hasattr(w, 'parent'):
                    w.parent = self
                tab_title = "📝 Заметка"
            elif title == "Таблица":
                w = TableEditorTab()
                if hasattr(w, 'parent'):
                    w.parent = self
                tab_title = "📊 Таблица"
            elif title == "Граф":
                w = GraphTab()
                if hasattr(w, 'parent'):
                    w.parent = self
                tab_title = "🕸️ Граф"
            elif title == "Задача":
                w = TaskTab()
                if hasattr(w, 'parent'):
                    w.parent = self
                tab_title = "✅ Задача"
            else:
                # Заглушка для других типов
                w = QWidget()
                layout = QVBoxLayout(w)
                te = QTextEdit()
                te.setPlainText(f"{title} — содержание (заглушка).")
                layout.addWidget(te)
                tab_title = title
            
            # Добавляем вкладку
            index = self.main_tab_widget.addTab(w, tab_title)
            self.main_tab_widget.setCurrentIndex(index)
            print(f"✅ Создана вкладка: {title}")
            
        except Exception as e:
            print(f"❌ Ошибка создания вкладки {title}: {e}")
            # Создаем простую заглушку при ошибке
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.addWidget(QLabel(f"Ошибка создания {title}: {e}"))
            self.main_tab_widget.addTab(w, f"❌ {title}")

    def rebuild_panel_actions_menu(self):
        """Создает меню для скрытия/показа панелей"""
        actions = []
        self._panel_actions.clear()
        
        for key, dock in self.dock_widgets.items():
            title = dock.windowTitle() or key
            act = QAction(title, self)
            act.setCheckable(True)
            act.setChecked(dock.isVisible())
            
            # Создаем замыкание для переключения видимости
            def make_toggler(dock_key=key):
                def toggle():
                    w = self.dock_widgets[dock_key]
                    visible = not w.isVisible()
                    w.setVisible(visible)
                    if visible:
                        w.raise_()
                return toggle
            
            act.triggered.connect(make_toggler())
            actions.append(act)
            self._panel_actions[key] = act
        
        self.top_bar.set_panels_menu(actions)

    def close_tab(self, index):
        """Закрывает вкладку"""
        if self.main_tab_widget.count() > 1:
            self.main_tab_widget.removeTab(index)

    def on_workspace_changed(self, workspace_name: str):
        """Обработчик изменения workspace"""
        self.settings.setValue(self.WORKSPACE_SETTINGS_KEY, workspace_name)
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Рабочее пространство: {workspace_name}", 2500)

    def open_profile(self):
        """Открывает диалог профиля"""
        try:
            dlg = ProfileDialog(self)
            dlg.exec()
        except Exception as e:
            print(f"⚠️ Ошибка открытия профиля: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть профиль: {e}")

    def apply_theme(self):
        """Применяет тему"""
        app = QtWidgets.QApplication.instance()
        if not app:
            return

        setup_app_theme(app, self.current_theme)
        self.top_bar.update_theme(self.current_theme)
        self._update_tools_panel_icons()
        self._force_style_update()

        if hasattr(self, "status_bar"):
            theme_name = "темная" if self.current_theme == "dark" else "светлая"
            self.status_bar.showMessage(f"Тема: {theme_name}", 2000)

    def _force_style_update(self):
        """Принудительно обновляет стили"""
        self.style().unpolish(self)
        self.style().polish(self)

        if self.centralWidget():
            self.centralWidget().style().unpolish(self.centralWidget())
            self.centralWidget().style().polish(self.centralWidget())

        self.top_bar.style().unpolish(self.top_bar)
        self.top_bar.style().polish(self.top_bar)

        for dock in self.dock_widgets.values():
            dock.style().unpolish(dock)
            dock.style().polish(dock)
            if dock.widget():
                dock.widget().style().unpolish(dock.widget())
                dock.widget().style().polish(dock.widget())

    def toggle_theme(self):
        """Переключает тему"""
        self.current_theme = self.theme_manager.toggle_theme()
        self.apply_theme()

# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    setup_app_theme(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()