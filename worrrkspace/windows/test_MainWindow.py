"""WoRRRkspace MainWindow - Clean Version"""

import sys
import warnings
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QPoint
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QToolButton, QTabWidget, QStatusBar, QMenu,
    QPushButton, QTextEdit, QDockWidget, QDialog, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QPalette, QColor

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class AppConfig:
    ORG_NAME: str = "worrrkspace_company"
    APP_NAME: str = "worrrkspace_app"
    WINDOW_TITLE: str = "WoRRRkspace"
    MIN_SIZE: tuple = (1000, 700)
    DEFAULT_SIZE: tuple = (1400, 900)
    TOPBAR_HEIGHT: int = 56
    ICON_SIZE: int = 24
    TOOL_ICON_SIZE: int = 20

@dataclass
class ColorScheme:
    """WoRRRkspace color palette"""
    BG_PRIMARY: str = "#141414"
    BG_SECONDARY: str = "#0f0f0f"
    ACCENT_BRIGHT: str = "#863eff"
    ACCENT_MEDIUM: str = "#5b2aad"
    ACCENT_DARK: str = "#4b238f"
    
    TEXT_LIGHT: str = "#ffffff"
    TEXT_MUTED: str = "#a0a0a0"
    BORDER_DARK: str = "#2a2a2a"
    BORDER_LIGHT: str = "#3a3a3a"

CONFIG = AppConfig()
COLORS = ColorScheme()

# =============================================================================
# PATH SETUP
# =============================================================================

def setup_paths():
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    worrrkspace_path = project_root / "worrrkspace"
    
    paths = [
        worrrkspace_path / "ui" / "widgets",
        worrrkspace_path / "ui" / "panels", 
        worrrkspace_path / "src" / "python",
    ]
    
    for p in paths:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

setup_paths()

# =============================================================================
# LAZY IMPORTS
# =============================================================================

class LazyImporter:
    _cache: Dict[str, Any] = {}
    _errors: Dict[str, str] = {}
    
    @classmethod
    def get(cls, module_name: str, class_name: str, fallback_factory: Callable = None):
        cache_key = f"{module_name}.{class_name}"
        
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            klass = getattr(module, class_name)
            cls._cache[cache_key] = klass
            print(f"[OK] {class_name}")
            return klass
        except Exception as e:
            cls._errors[cache_key] = str(e)
            print(f"[WARN] {class_name}: {e}")
            
            if fallback_factory:
                fallback = fallback_factory()
                cls._cache[cache_key] = fallback
                return fallback
            return None
    
    @classmethod
    def get_errors(cls) -> Dict[str, str]:
        return cls._errors.copy()

# =============================================================================
# ICON MANAGER
# =============================================================================

class IconManager:
    _available: bool = False
    _tabler: Any = None
    _outline: Any = None
    _cache: Dict[tuple, QIcon] = {}
    
    ICONS = {
        "theme_light": "SUN",
        "theme_dark": "MOON",
        "profile": "USER_CIRCLE",
        "menu": "MENU_2",
        "table": "TABLE",
        "note": "NOTE",
        "graph": "CHART_ARCS_3",
        "chart": "CHART_ARCS_3",
        "task": "CHECKLIST",
        "diagram": "HIERARCHY_2",
        "save": "DEVICE_FLOPPY",
        "settings": "SETTINGS",
        "folders": "FOLDERS",
        "tools": "TOOLS",
        "chat": "MESSAGE_CHATBOT",
        "logs": "TERMINAL_2",
        "add": "PLUS",
        "delete": "TRASH",
        "edit": "EDIT",
        "close": "X",
    }
    
    @classmethod
    def init(cls):
        try:
            from pytablericons import TablerIcons, OutlineIcon
            cls._tabler = TablerIcons
            cls._outline = OutlineIcon
            cls._available = True
            print("[OK] PyTablerIcons")
        except ImportError as e:
            print(f"[WARN] PyTablerIcons: {e}")
    
    @classmethod
    def get(cls, key: str, size: int = 24, color: str = "#ffffff") -> QIcon:
        if not cls._available:
            return QIcon()
        
        cache_key = (key, size, color)
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        icon_name = cls.ICONS.get(key)
        if not icon_name:
            return QIcon()
        
        try:
            icon_enum = getattr(cls._outline, icon_name, None)
            if icon_enum:
                pixmap = cls._tabler.load(icon_enum, size=size, color=color).toqpixmap()
                qicon = QIcon(pixmap)
                cls._cache[cache_key] = qicon
                return qicon
        except Exception:
            pass
        
        return QIcon()
    
    @classmethod
    def themed(cls, theme: str, key: str, size: int = 24) -> QIcon:
        color = COLORS.TEXT_LIGHT if theme == "dark" else "#000000"
        return cls.get(key, size, color)
    
    @classmethod
    def accent(cls, key: str, size: int = 24) -> QIcon:
        return cls.get(key, size, COLORS.ACCENT_BRIGHT)

IconManager.init()

# =============================================================================
# STYLESHEETS
# =============================================================================

class StyleSheets:
    
    @staticmethod
    def dark_theme() -> str:
        return f"""
            QMainWindow {{
                background-color: {COLORS.BG_PRIMARY};
            }}
            
            QWidget {{
                background-color: {COLORS.BG_PRIMARY};
                color: {COLORS.TEXT_LIGHT};
                font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
            }}
            
            QDockWidget {{
                background-color: {COLORS.BG_SECONDARY};
                border: 1px solid {COLORS.BORDER_DARK};
                titlebar-close-icon: none;
            }}
            
            QDockWidget::title {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                padding: 8px;
                border-bottom: 1px solid {COLORS.BORDER_DARK};
            }}
            
            QTabWidget::pane {{
                background-color: {COLORS.BG_PRIMARY};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 4px;
            }}
            
            QTabBar::tab {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_MUTED};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {COLORS.ACCENT_DARK};
                color: {COLORS.TEXT_LIGHT};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS.BORDER_LIGHT};
            }}
            
            QPushButton {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS.ACCENT_DARK};
                border-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QToolButton {{
                background-color: transparent;
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 6px;
                padding: 6px;
            }}
            
            QToolButton:hover {{
                background-color: {COLORS.ACCENT_DARK};
                border-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QComboBox {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 200px;
            }}
            
            QComboBox:hover {{
                border-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                selection-background-color: {COLORS.ACCENT_DARK};
            }}
            
            QTextEdit, QPlainTextEdit {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QLineEdit {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {COLORS.ACCENT_BRIGHT};
            }}
            
            QStatusBar {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_MUTED};
                border-top: 1px solid {COLORS.BORDER_DARK};
            }}
            
            QMenu {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {COLORS.ACCENT_DARK};
            }}
            
            QScrollBar:vertical {{
                background-color: {COLORS.BG_PRIMARY};
                width: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {COLORS.BORDER_LIGHT};
                border-radius: 5px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QScrollBar:horizontal {{
                background-color: {COLORS.BG_PRIMARY};
                height: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {COLORS.BORDER_LIGHT};
                border-radius: 5px;
                min-width: 30px;
            }}
            
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0px;
                height: 0px;
            }}
            
            QTableWidget {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                gridline-color: {COLORS.BORDER_DARK};
                border: 1px solid {COLORS.BORDER_DARK};
            }}
            
            QTableWidget::item:selected {{
                background-color: {COLORS.ACCENT_DARK};
            }}
            
            QHeaderView::section {{
                background-color: {COLORS.BG_PRIMARY};
                color: {COLORS.TEXT_LIGHT};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS.BORDER_DARK};
            }}
            
            QTreeView, QListView {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 4px;
            }}
            
            QTreeView::item:selected, QListView::item:selected {{
                background-color: {COLORS.ACCENT_DARK};
            }}
            
            QTreeView::item:hover, QListView::item:hover {{
                background-color: {COLORS.BORDER_LIGHT};
            }}
            
            QSplitter::handle {{
                background-color: {COLORS.BORDER_DARK};
            }}
            
            QSplitter::handle:hover {{
                background-color: {COLORS.ACCENT_MEDIUM};
            }}
        """
    
    @staticmethod
    def light_theme() -> str:
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QWidget {
                background-color: #ffffff;
                color: #1a1a1a;
            }
            
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #863eff;
            }
        """

# =============================================================================
# FALLBACK FACTORIES
# =============================================================================

def create_fallback_widget(title: str, content: str = "") -> type:
    class FallbackWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(title))
            if content:
                te = QTextEdit()
                te.setPlainText(content)
                layout.addWidget(te)
    return FallbackWidget

def create_fallback_dock(title: str) -> type:
    class FallbackDock(QDockWidget):
        def __init__(self, parent=None):
            super().__init__(title, parent)
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.addWidget(QLabel(title))
            self.setWidget(w)
    return FallbackDock

def create_fallback_tools_panel() -> type:
    class FallbackToolsPanel(QDockWidget):
        def __init__(self, parent=None):
            super().__init__("Tools", parent)
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            self.btn_table = QPushButton("Таблица")
            self.btn_note = QPushButton("Заметка")  
            self.btn_chart = QPushButton("Граф")
            self.btn_task = QPushButton("Задача")
            self.btn_diagramm = QPushButton("Диаграмма")
            
            for btn in [self.btn_table, self.btn_note, self.btn_chart, 
                        self.btn_task, self.btn_diagramm]:
                btn.setMinimumHeight(40)
                layout.addWidget(btn)
            
            layout.addStretch()
            self.setWidget(widget)
    return FallbackToolsPanel

# =============================================================================
# IMPORTS
# =============================================================================

# Theme
ThemeManager = LazyImporter.get("theme_manager", "ThemeManager")
if not ThemeManager:
    class ThemeManager:
        def __init__(self, **kwargs):
            self.current_theme = "dark"
        def toggle_theme(self):
            self.current_theme = "light" if self.current_theme == "dark" else "dark"
            return self.current_theme

setup_app_theme_func = LazyImporter.get("theme_manager", "setup_app_theme")

# Widgets
MarkdownNoteTab = LazyImporter.get(
    "markdown_editor", "MarkdownNoteTab",
    lambda: create_fallback_widget("Markdown Editor", "Enter text...")
)

TableEditorTab = LazyImporter.get(
    "table_editor", "TableEditorTab",
    lambda: create_fallback_widget("Table Editor")
)

GraphTab = LazyImporter.get(
    "graph_editor", "GraphTab",
    lambda: create_fallback_widget("Graph Editor", "Graph visualization")
)

TaskTab = LazyImporter.get(
    "task_editor", "TaskTab", 
    lambda: create_fallback_widget("Task Editor")
)

DiagramTab = LazyImporter.get(
    "diagram_editor", "DiagramTab",
    lambda: create_fallback_widget("Diagram Editor", "Diagram visualization")
)

# Dialogs
ProfileDialog = LazyImporter.get("base_widgets", "ProfileDialog")
if not ProfileDialog:
    class ProfileDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Profile")
            self.setStyleSheet(StyleSheets.dark_theme())
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("User Profile"))
            btn = QPushButton("Close")
            btn.clicked.connect(self.accept)
            layout.addWidget(btn)

# Panels
SolutionExplorer = LazyImporter.get(
    "solution_explorer", "SolutionExplorer",
    lambda: create_fallback_dock("Solution Explorer")
)

ToolsPanel = LazyImporter.get(
    "tools_panel", "ToolsPanel",
    create_fallback_tools_panel
)

ChatPanel = LazyImporter.get(
    "chat_panel", "ChatPanel",
    lambda: create_fallback_dock("Chat")
)

LogsPanel = LazyImporter.get(
    "logs_panel", "LogsPanel", 
    lambda: create_fallback_dock("Logs")
)

# =============================================================================
# TOP BAR
# =============================================================================

class TopBar(QWidget):
    workspace_changed = pyqtSignal(str)
    profile_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()
    
    WORKSPACES = ["Default", "Development", "Analytics", "Custom"]

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._theme = theme
        self.setFixedHeight(CONFIG.TOPBAR_HEIGHT)
        self._setup_ui()
        self._update_icons()
        self._apply_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        self.theme_btn = self._create_button("Toggle theme")
        self.theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(self.theme_btn)

        layout.addStretch()

        self.workspace_combo = QComboBox()
        self.workspace_combo.addItems(self.WORKSPACES)
        self.workspace_combo.currentTextChanged.connect(self.workspace_changed.emit)
        layout.addWidget(self.workspace_combo)

        layout.addStretch()

        self.profile_btn = self._create_button("Profile")
        self.profile_btn.clicked.connect(self.profile_requested.emit)
        layout.addWidget(self.profile_btn)

        self.panels_btn = self._create_button("Panels")
        self.panel_menu = QMenu(self)
        self.panels_btn.clicked.connect(self._show_panel_menu)
        layout.addWidget(self.panels_btn)

    def _create_button(self, tooltip: str) -> QToolButton:
        btn = QToolButton()
        btn.setToolTip(tooltip)
        btn.setAutoRaise(True)
        btn.setFixedSize(40, 40)
        return btn

    def _show_panel_menu(self):
        if self.panel_menu.actions():
            pos = self.panels_btn.mapToGlobal(QPoint(0, self.panels_btn.height()))
            self.panel_menu.exec(pos)

    def _update_icons(self):
        color = COLORS.ACCENT_BRIGHT
        icon_key = "theme_dark" if self._theme == "light" else "theme_light"
        self.theme_btn.setIcon(IconManager.get(icon_key, 24, color))
        self.profile_btn.setIcon(IconManager.get("profile", 24, color))
        self.panels_btn.setIcon(IconManager.get("menu", 24, color))

    def _apply_style(self):
        self.setStyleSheet(f"""
            TopBar {{
                background-color: {COLORS.BG_SECONDARY};
                border-bottom: 1px solid {COLORS.BORDER_DARK};
            }}
            
            QToolButton {{
                background-color: transparent;
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 8px;
            }}
            
            QToolButton:hover {{
                background-color: {COLORS.ACCENT_DARK};
                border-color: {COLORS.ACCENT_MEDIUM};
            }}
            
            QComboBox {{
                background-color: {COLORS.BG_PRIMARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                border-radius: 8px;
                padding: 8px 16px;
                min-width: 200px;
            }}
            
            QComboBox:hover {{
                border-color: {COLORS.ACCENT_BRIGHT};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {COLORS.BG_SECONDARY};
                color: {COLORS.TEXT_LIGHT};
                border: 1px solid {COLORS.BORDER_DARK};
                selection-background-color: {COLORS.ACCENT_DARK};
            }}
        """)

    def set_theme(self, theme: str):
        self._theme = theme
        self._update_icons()

    def set_panels_menu(self, actions: list):
        self.panel_menu.clear()
        for act in actions:
            self.panel_menu.addAction(act)

# =============================================================================
# TAB FACTORY
# =============================================================================

class TabFactory:
    TABS = {
        "Note": ("Note", MarkdownNoteTab),
        "Table": ("Table", TableEditorTab),
        "Graph": ("Graph", GraphTab),
        "Task": ("Task", TaskTab),
        "Diagram": ("Diagram", DiagramTab),
    }
    
    @classmethod
    def create(cls, tab_type: str, parent=None) -> tuple:
        if tab_type not in cls.TABS:
            return None, f"Unknown type: {tab_type}"
        
        title, widget_class = cls.TABS[tab_type]
        
        if widget_class is None:
            return None, f"Class {tab_type} not loaded"
        
        try:
            widget = widget_class(parent)
            print(f"[OK] Created: {tab_type}")
            return widget, title
        except Exception as e:
            error_msg = f"Error creating {tab_type}: {e}"
            print(f"[ERROR] {error_msg}")
            
            fallback = QWidget(parent)
            layout = QVBoxLayout(fallback)
            layout.addWidget(QLabel(error_msg))
            
            errors = LazyImporter.get_errors()
            if errors:
                layout.addWidget(QLabel("Import errors:"))
                for key, err in errors.items():
                    layout.addWidget(QLabel(f"  - {key}: {err}"))
            
            return fallback, f"Error: {tab_type}"

# =============================================================================
# MAIN WINDOW
# =============================================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.settings = QSettings(CONFIG.ORG_NAME, CONFIG.APP_NAME)
        self.theme_manager = ThemeManager(
            organization=CONFIG.ORG_NAME, 
            application=CONFIG.APP_NAME
        )
        self.current_theme = getattr(self.theme_manager, 'current_theme', 'dark')
        self.dock_widgets: Dict[str, QDockWidget] = {}
        
        self._init_window()

    def _init_window(self):
        self.setWindowTitle(CONFIG.WINDOW_TITLE)
        self.setMinimumSize(*CONFIG.MIN_SIZE)
        self.resize(*CONFIG.DEFAULT_SIZE)
        self._center_window()
        
        self._setup_central_widget()
        self._setup_top_bar()
        self._setup_panels()
        self._setup_connections()
        self._apply_theme()
        
        self._log_status()

    def _center_window(self):
        if screen := self.screen():
            geom = screen.geometry()
            self.move(geom.center() - self.rect().center())

    def _setup_central_widget(self):
        ui_file = Path(__file__).parent / "MainWindow.ui"
        if ui_file.exists():
            try:
                uic.loadUi(ui_file, self)
                print("[OK] Loaded MainWindow.ui")
                return
            except Exception as e:
                print(f"[WARN] UI file: {e}")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setTabsClosable(True)
        self.main_tab_widget.setDocumentMode(True)
        layout.addWidget(self.main_tab_widget)
        
        self.setStatusBar(QStatusBar())

    def _setup_top_bar(self):
        self.top_bar = TopBar(theme=self.current_theme)
        self.setMenuWidget(self.top_bar)
        
        saved = self.settings.value("app/workspace", "")
        if saved:
            idx = self.top_bar.workspace_combo.findText(saved)
            if idx >= 0:
                self.top_bar.workspace_combo.setCurrentIndex(idx)

    def _setup_panels(self):
        panels_config = [
            ("solution_explorer", SolutionExplorer, Qt.DockWidgetArea.LeftDockWidgetArea),
            ("tools", ToolsPanel, Qt.DockWidgetArea.LeftDockWidgetArea),
            ("chat", ChatPanel, Qt.DockWidgetArea.RightDockWidgetArea),
            ("logs", LogsPanel, Qt.DockWidgetArea.BottomDockWidgetArea),
        ]
        
        for key, panel_class, area in panels_config:
            try:
                panel = panel_class(self)
                self.addDockWidget(area, panel)
                self.dock_widgets[key] = panel
            except Exception as e:
                print(f"[WARN] Panel {key}: {e}")
        
        if "solution_explorer" in self.dock_widgets and "tools" in self.dock_widgets:
            try:
                self.tabifyDockWidget(
                    self.dock_widgets["solution_explorer"],
                    self.dock_widgets["tools"]
                )
                self.dock_widgets["solution_explorer"].raise_()
            except Exception:
                pass
        
        self._rebuild_panels_menu()

    def _setup_connections(self):
        self.top_bar.workspace_changed.connect(self._on_workspace_changed)
        self.top_bar.theme_toggle_requested.connect(self._toggle_theme)
        self.top_bar.profile_requested.connect(self._open_profile)
        
        if hasattr(self, "main_tab_widget"):
            self.main_tab_widget.tabCloseRequested.connect(self._close_tab)
        
        self._connect_tools_panel()

    def _connect_tools_panel(self):
        tools = self.dock_widgets.get("tools")
        if not tools:
            print("[WARN] ToolsPanel not found")
            return
        
        # Fixed mapping with correct button names
        buttons = {
            "btn_table": "Table",
            "btn_note": "Note",
            "btn_chart": "Graph",       # btn_chart -> Graph
            "btn_task": "Task",
            "btn_diagramm": "Diagram",  # btn_diagramm -> Diagram
        }
        
        connected = 0
        for attr, tab_type in buttons.items():
            btn = getattr(tools, attr, None)
            if btn:
                btn.clicked.connect(lambda checked, t=tab_type: self._create_tab(t))
                connected += 1
                print(f"  [OK] {attr} -> {tab_type}")
            else:
                print(f"  [WARN] {attr} not found")
        
        print(f"[OK] Connected {connected}/{len(buttons)} tool buttons")

    def _create_tab(self, tab_type: str):
        if not hasattr(self, "main_tab_widget"):
            QMessageBox.warning(self, "Error", "TabWidget not initialized")
            return
        
        print(f"[INFO] Creating tab: {tab_type}")
        
        widget, title = TabFactory.create(tab_type, self)
        
        if widget:
            index = self.main_tab_widget.addTab(widget, title)
            self.main_tab_widget.setCurrentIndex(index)
            self.statusBar().showMessage(f"Created: {title}", 2000)

    def _close_tab(self, index: int):
        if self.main_tab_widget.count() > 0:
            self.main_tab_widget.removeTab(index)

    def _on_workspace_changed(self, name: str):
        self.settings.setValue("app/workspace", name)
        self.statusBar().showMessage(f"Workspace: {name}", 2000)

    def _open_profile(self):
        try:
            dlg = ProfileDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _toggle_theme(self):
        self.current_theme = self.theme_manager.toggle_theme()
        self._apply_theme()

    def _apply_theme(self):
        app = QtWidgets.QApplication.instance()
        if not app:
            return
        
        if self.current_theme == "dark":
            app.setStyleSheet(StyleSheets.dark_theme())
        else:
            app.setStyleSheet(StyleSheets.light_theme())
        
        self.top_bar.set_theme(self.current_theme)
        self._update_tools_icons()
        
        theme_name = "dark" if self.current_theme == "dark" else "light"
        self.statusBar().showMessage(f"Theme: {theme_name}", 2000)

    def _update_tools_icons(self):
        tools = self.dock_widgets.get("tools")
        if not tools:
            return
        
        icons = [
            ("btn_table", "table"),
            ("btn_note", "note"),
            ("btn_chart", "chart"),
            ("btn_task", "task"),
            ("btn_diagramm", "diagram"),
        ]
        
        for attr, icon_key in icons:
            btn = getattr(tools, attr, None)
            if btn:
                icon = IconManager.get(icon_key, 20, COLORS.ACCENT_BRIGHT)
                if not icon.isNull():
                    btn.setIcon(icon)

    def _rebuild_panels_menu(self):
        actions = []
        
        for key, dock in self.dock_widgets.items():
            act = QAction(dock.windowTitle() or key, self)
            act.setCheckable(True)
            act.setChecked(dock.isVisible())
            
            def make_toggle(k=key):
                def toggle():
                    w = self.dock_widgets[k]
                    w.setVisible(not w.isVisible())
                    if w.isVisible():
                        w.raise_()
                return toggle
            
            act.triggered.connect(make_toggle())
            actions.append(act)
        
        self.top_bar.set_panels_menu(actions)

    def _log_status(self):
        errors = LazyImporter.get_errors()
        if errors:
            print("\n[WARN] Import errors:")
            for key, err in errors.items():
                print(f"   {key}: {err}")
        
        print(f"\n[OK] {CONFIG.WINDOW_TITLE} started")

# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(CONFIG.APP_NAME)
    app.setOrganizationName(CONFIG.ORG_NAME)
    app.setStyle("Fusion")
    
    # Apply dark theme by default
    app.setStyleSheet(StyleSheets.dark_theme())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()