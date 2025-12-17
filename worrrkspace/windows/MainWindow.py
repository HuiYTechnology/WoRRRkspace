"""Отточить дизигне"""

import sys
import os
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*sipPyTypeDict.*"
)

from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QPoint
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QToolButton, QTabWidget, QStatusBar,
    QMenu, QPushButton, QTextEdit, QLineEdit, QSplitter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QAction

try:
    from ..core.python.theme_util import SystemThemeDetector
    from ..core.python.theme_manager import setup_app_theme, ThemeManager
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: добавляем путь вручную для отладки
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    src_python_path = project_root / "worrrkspace" / "src" / "python"
    print(f"Trying to add path: {src_python_path}")
    sys.path.insert(0, str(src_python_path))
    from theme_util import SystemThemeDetector
    from theme_manager import setup_app_theme, ThemeManager

# Импортируем виджеты из отдельных модулей
try:
    from ..ui.widgets.base_widgets import ProfileDialog
    from ..ui.widgets.markdown_editor import MarkdownNoteTab
    from ..ui.widgets.table_editor import TableEditorTab
    from ..ui.widgets.graph_editor import GraphTab
    from ..ui.widgets.task_editor import TaskTab
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: добавляем путь вручную для отладки
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    widgets_python_path = project_root / "worrrkspace" / "ui" / "widgets"
    print(f"Trying to add path: {widgets_python_path}")
    sys.path.insert(0, str(widgets_python_path))
    from base_widgets import ProfileDialog
    from markdown_editor import MarkdownNoteTab
    from table_editor import TableEditorTab
    from graph_editor import GraphTab
    from task_editor import TaskTab

# Импортируем панели из новой директории
try:
    from ..ui.panels import SolutionExplorer, ToolsPanel, ChatPanel, LogsPanel
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: добавляем путь вручную для отладки
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    panels_python_path = project_root / "worrrkspace" / "ui" / "panels"
    print(f"Trying to add path: {panels_python_path}")
    sys.path.insert(0, str(panels_python_path))
    from solution_explorer import SolutionExplorer
    from tools_panel import ToolsPanel
    from chat_panel import ChatPanel
    from logs_panel import LogsPanel
    


class DraggableTabBar(QtWidgets.QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)  # Включаем стандартное перемещение для ЛКМ
        self.setExpanding(False)

        # Переменные для перетаскивания ПКМ
        self.right_drag_start_position = None
        self.right_drag_current_position = None
        self.right_dragging = False
        self.right_drag_index = -1
        self.right_drag_pixmap = None

    def mousePressEvent(self, event):
        # Обрабатываем ПКМ для межоконного перетаскивания
        if event.button() == Qt.MouseButton.RightButton:
            self.right_drag_start_position = event.position().toPoint()
            self.right_drag_current_position = self.right_drag_start_position
            self.right_dragging = True
            self.right_drag_index = self.tabAt(self.right_drag_start_position)

            # Создаем pixmap для визуальной обратной связи при перетаскивании
            if self.right_drag_index >= 0:
                rect = self.tabRect(self.right_drag_index)
                self.right_drag_pixmap = self.grab(rect)

            # Не вызываем родительский метод для ПКМ, чтобы избежать конфликтов
            return

        # Для ЛКМ и других кнопок вызываем стандартную обработку
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Обрабатываем перетаскивание ПКМ
        if self.right_dragging and event.buttons() & Qt.MouseButton.RightButton:
            self.right_drag_current_position = event.position().toPoint()

            # Если переместились достаточно далеко от начальной точки, начинаем перетаскивание
            if (
                    self.right_drag_start_position - self.right_drag_current_position).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                self.startRightDrag()
                return

        # Для других случаев вызываем стандартную обработку
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Сбрасываем состояние перетаскивания ПКМ
        if event.button() == Qt.MouseButton.RightButton:
            self.right_dragging = False
            self.right_drag_start_position = None
            self.right_drag_current_position = None
            self.right_drag_index = -1
            self.right_drag_pixmap = None
            return

        super().mouseReleaseEvent(event)

    def startRightDrag(self):
        if self.right_drag_index < 0:
            return

        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()

        # Сохраняем информацию о вкладке
        tab_data = QtCore.QByteArray()
        stream = QtCore.QDataStream(tab_data, QtCore.QIODevice.OpenModeFlag.WriteOnly)
        stream.writeQString(self.tabText(self.right_drag_index))
        stream.writeInt(self.right_drag_index)

        mime_data.setData("application/x-tabwidget", tab_data)
        drag.setMimeData(mime_data)

        # Устанавливаем визуальную обратную связь - pixmap вкладки
        if self.right_drag_pixmap:
            drag.setPixmap(self.right_drag_pixmap)
            # Устанавливаем точку "захвата" - где пользователь зажал вкладку
            drag.setHotSpot(self.right_drag_current_position - self.tabRect(self.right_drag_index).topLeft())

        # Запускаем перетаскивание
        result = drag.exec(Qt.DropAction.MoveAction)

        # Если перетаскивание завершилось вне окна, создаем новое окно
        if result == Qt.DropAction.IgnoreAction:
            self.createNewWindowWithTab()

    def createNewWindowWithTab(self):
        """Создает новое окно с текущей вкладкой"""
        if self.right_drag_index < 0:
            return

        try:
            # Получаем данные о вкладке
            current_index = self.currentIndex()
            if current_index < 0:
                return

            widget = self.parent().widget(current_index)
            title = self.tabText(current_index)

            # Создаем новое окно
            new_window = MainWindow()

            # Удаляем вкладку из текущего окна
            self.parent().removeTab(current_index)

            # Добавляем в новое окно
            new_window.main_tab_widget.addTab(widget, title)
            new_window.main_tab_widget.setCurrentWidget(widget)

            # Показываем новое окно рядом с курсором
            global_pos = self.mapToGlobal(self.right_drag_current_position)
            new_window.move(global_pos.x() - 100, global_pos.y() - 50)
            new_window.show()

        except Exception as e:
            print(f"Error creating new window: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            tab_data = event.mimeData().data("application/x-tabwidget")
            stream = QtCore.QDataStream(tab_data, QtCore.QIODevice.OpenModeFlag.ReadOnly)
            title = stream.readQString()
            source_index = stream.readInt()

            # Находим позицию для вставки
            drop_pos = event.position().toPoint()
            insert_index = self.count()
            for i in range(self.count()):
                if self.tabRect(i).contains(drop_pos):
                    insert_index = i
                    break

            # Если это перетаскивание из другого окна
            if event.source() != self:
                # Получаем виджет из исходного окна
                source_widget = None
                source_parent = event.source().parent()
                if hasattr(source_parent, 'widget'):
                    source_widget = source_parent.widget(source_index)

                if source_widget:
                    # Добавляем вкладку в текущий TabWidget
                    self.parent().insertTab(insert_index, source_widget, title)
                    self.parent().setCurrentIndex(insert_index)

                    # Удаляем вкладку из исходного TabWidget
                    event.source().parent().removeTab(source_index)

            event.acceptProposedAction()


class DraggableTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(DraggableTabBar(self))
        self.setDocumentMode(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setTabsClosable(True)
        self.setMovable(True)  # Включаем стандартное перемещение для ЛКМ
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-tabwidget"):
            tab_data = event.mimeData().data("application/x-tabwidget")
            stream = QtCore.QDataStream(tab_data, QtCore.QIODevice.OpenModeFlag.ReadOnly)
            title = stream.readQString()
            source_index = stream.readInt()

            # Если перетаскивание из другого окна
            if event.source() != self.tabBar():
                # Получаем виджет из исходного окна
                source_widget = None
                if hasattr(event.source(), 'parent') and hasattr(event.source().parent(), 'widget'):
                    source_widget = event.source().parent().widget(source_index)

                if source_widget:
                    # Добавляем вкладку
                    self.addTab(source_widget, title)
                    self.setCurrentWidget(source_widget)

                    # Удаляем вкладку из исходного TabWidget
                    event.source().parent().removeTab(source_index)

            event.acceptProposedAction()


class TopBar(QWidget):
    workspace_changed = pyqtSignal(str)
    profile_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.panel_menu_button = None
        self.panel_menu = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(8)

        self.theme_button = QToolButton()
        self.theme_button.setText("🌓")
        self.theme_button.setToolTip("Переключить тему")
        self.theme_button.setAutoRaise(True)
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(self.theme_button)

        layout.addStretch()

        self.workspace_combo = QComboBox()
        self.workspace_combo.setMinimumWidth(260)
        self.workspace_combo.addItems(["По умолчанию", "Разработка", "Аналитика", "Пользовательское"])
        self.workspace_combo.setToolTip("Выберите рабочее пространство")

        right_container = QHBoxLayout()
        right_container.setSpacing(6)

        self.profile_button = QToolButton()
        try:
            self.profile_button.setIcon(QIcon.fromTheme("user"))
        except Exception:
            pass
        self.profile_button.setText("Профиль")
        self.profile_button.setToolTip("Открыть профиль")
        self.profile_button.setAutoRaise(True)

        self.panel_menu_button = QToolButton()
        try:
            self.panel_menu_button.setIcon(QIcon.fromTheme("view-list"))
        except Exception:
            pass
        self.panel_menu_button.setText("Панели")
        self.panel_menu_button.setToolTip("Показать/скрыть панели")
        self.panel_menu_button.setAutoRaise(True)

        self.panel_menu = QMenu(self)

        def _show_panel_menu():
            btn = self.panel_menu_button
            pos = btn.mapToGlobal(QPoint(0, btn.height()))
            if self.panel_menu.actions():
                self.panel_menu.exec(pos)

        self.panel_menu_button.clicked.connect(_show_panel_menu)

        right_container.addWidget(self.profile_button)
        right_container.addWidget(self.panel_menu_button)

        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.workspace_combo)
        center_layout.addStretch()

        layout.addWidget(center_widget)
        layout.addLayout(right_container)
        layout.addStretch()

        self.workspace_combo.currentTextChanged.connect(self.workspace_changed.emit)

    def set_panels_menu(self, actions):
        self.panel_menu.clear()
        for act in actions:
            self.panel_menu.addAction(act)

    def update_theme_button(self, theme):
        if theme == "dark":
            self.theme_button.setText("☀️")
            self.theme_button.setToolTip("Переключить на светлую тему")
        else:
            self.theme_button.setText("🌙")
            self.theme_button.setToolTip("Переключить на темную тему")


class MainWindow(QMainWindow):
    WORKSPACE_SETTINGS_KEY = "app/worrrkspace"

    def __init__(self):
        super().__init__()
        self.settings = QSettings("worrrkspace_company", "worrrkspace_app")

        self.theme_manager = ThemeManager(organization="worrrkspace_company", application="worrrkspace_app")
        self.current_theme = self.theme_manager.current_theme

        self.dock_widgets = {}
        self._panel_actions = {}
        self.setup_window()
        self.load_ui()
        self.setup_ui()
        self.apply_theme()
        self.setup_connections()

    def setup_window(self):
        self.setWindowTitle("WoRRRkspace")
        self.setMinimumSize(1000, 700)
        self.resize(1400, 900)
        screen = self.screen()
        if screen:
            geom = screen.geometry()
            center = geom.center()
            self.move(center - self.rect().center())

    def load_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "MainWindow.ui")
        if os.path.exists(ui_file):
            try:
                uic.loadUi(ui_file, self)
                self.clear_builtin_styles()
                # Заменяем стандартный QTabWidget на наш DraggableTabWidget
                self.replace_tab_widget()
            except Exception as e:
                print(f"Error loading UI file: {e}")
                self.setup_fallback_ui()
        else:
            self.setup_fallback_ui()

    def replace_tab_widget(self):
        """Заменяет стандартный QTabWidget на наш DraggableTabWidget"""
        if hasattr(self, 'main_tab_widget') and isinstance(self.main_tab_widget, QtWidgets.QTabWidget):
            old_tab_widget = self.main_tab_widget

            # Создаем новый кастомный виджет вкладок
            new_tab_widget = DraggableTabWidget()

            # Переносим все вкладки из старого виджета
            for i in range(old_tab_widget.count()):
                widget = old_tab_widget.widget(i)
                title = old_tab_widget.tabText(i)
                new_tab_widget.addTab(widget, title)

            # Заменяем в layout
            if hasattr(self, 'verticalLayout'):
                layout = self.verticalLayout
                index = layout.indexOf(old_tab_widget)
                layout.removeWidget(old_tab_widget)
                layout.insertWidget(index, new_tab_widget)
                self.main_tab_widget = new_tab_widget

                # Подключаем обработчик закрытия вкладок
                self.main_tab_widget.tabCloseRequested.connect(self.close_tab)

                old_tab_widget.deleteLater()

    def clear_builtin_styles(self):
        self.setStyleSheet("")
        if hasattr(self, 'centralwidget'):
            self.centralwidget.setStyleSheet("")
        if hasattr(self, 'main_tab_widget'):
            self.main_tab_widget.setStyleSheet("")
        if hasattr(self, 'welcome_tab'):
            self.welcome_tab.setStyleSheet("")
        if hasattr(self, 'settings_tab'):
            self.settings_tab.setStyleSheet("")
        for child in self.findChildren(QtWidgets.QWidget):
            child.setStyleSheet("")

    def setup_fallback_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_tab_widget = DraggableTabWidget()  # Используем наш кастомный виджет
        self.main_tab_widget.setTabsClosable(True)
        layout.addWidget(self.main_tab_widget)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_ui(self):
        self.top_bar = TopBar()
        self.setMenuWidget(self.top_bar)
        self.top_bar.update_theme_button(self.current_theme)

        self.create_panels()

        if not hasattr(self, "status_bar") or self.statusBar() is None:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)

        saved_ws = self.settings.value(self.WORKSPACE_SETTINGS_KEY, "")
        if saved_ws:
            idx = self.top_bar.workspace_combo.findText(saved_ws)
            if idx >= 0:
                self.top_bar.workspace_combo.setCurrentIndex(idx)

        self.rebuild_panel_actions_menu()

    def create_panels(self):
        # Создаем панели из импортированных классов
        self.solution_explorer = SolutionExplorer(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.solution_explorer)
        self.dock_widgets["solution_explorer"] = self.solution_explorer

        self.tools_panel = ToolsPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tools_panel)
        self.dock_widgets["tools"] = self.tools_panel

        self.chat_panel = ChatPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chat_panel)
        self.dock_widgets["chat"] = self.chat_panel

        self.logs_panel = LogsPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.logs_panel)
        self.dock_widgets["logs"] = self.logs_panel

        try:
            self.tabifyDockWidget(self.solution_explorer, self.tools_panel)
            self.solution_explorer.raise_()
        except Exception:
            pass

        for key, dock in self.dock_widgets.items():
            dock.visibilityChanged.connect(self.rebuild_panel_actions_menu)

    def setup_connections(self):
        self.top_bar.workspace_changed.connect(self.on_workspace_changed)
        self.top_bar.profile_button.clicked.connect(self.open_profile)
        self.top_bar.theme_toggle_requested.connect(self.toggle_theme)

        if hasattr(self, "tools_panel"):
            tp = self.tools_panel
            tp.btn_table.clicked.connect(lambda: self._open_placeholder_tab("Таблица"))
            tp.btn_note.clicked.connect(lambda: self._open_placeholder_tab("Заметка"))
            # tp.btn_diagramm.clicked.connect(lambda: self._open_placeholder_tab("Диаграмма"))
            tp.btn_chart.clicked.connect(lambda: self._open_placeholder_tab("Граф"))
            tp.btn_task.clicked.connect(lambda: self._open_placeholder_tab("Задача"))

        if hasattr(self, "main_tab_widget"):
            try:
                self.main_tab_widget.tabCloseRequested.connect(self.close_tab)
            except Exception:
                pass

    def _open_placeholder_tab(self, title: str):
        if not hasattr(self, "main_tab_widget"):
            return

        if title == "Заметка":
            w = MarkdownNoteTab()
            w.parent = self
            self.main_tab_widget.addTab(w, "📝 " + title)
            self.main_tab_widget.setCurrentWidget(w)
        elif title == "Таблица":
            w = TableEditorTab()
            w.parent = self
            self.main_tab_widget.addTab(w, "📊 " + title)
            self.main_tab_widget.setCurrentWidget(w)
        elif title == "Граф":
            w = GraphTab()
            w.parent = self
            self.main_tab_widget.addTab(w, "🕸️ " + title)
            self.main_tab_widget.setCurrentWidget(w)
        elif title == "Задача":
            w = TaskTab()
            w.parent = self
            self.main_tab_widget.addTab(w, "✅ " + title)
            self.main_tab_widget.setCurrentWidget(w)
        else:
            w = QWidget()
            l = QVBoxLayout(w)
            te = QTextEdit()
            te.setReadOnly(False)
            te.setPlainText(f"{title} — содержание (заглушка).")
            l.addWidget(te)
            self.main_tab_widget.addTab(w, title)
            self.main_tab_widget.setCurrentWidget(w)

    def rebuild_panel_actions_menu(self):
        actions = []
        self._panel_actions.clear()
        for key, dock in self.dock_widgets.items():
            title = dock.windowTitle() or key
            act = QAction(title, self)
            act.setCheckable(True)
            act.setChecked(dock.isVisible())

            def make_toggler(d=key):
                def toggle():
                    w = self.dock_widgets[d]
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
        if self.main_tab_widget.count() > 1:
            self.main_tab_widget.removeTab(index)

    def on_workspace_changed(self, workspace_name: str):
        self.settings.setValue(self.WORKSPACE_SETTINGS_KEY, workspace_name)
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Рабочее пространство: {workspace_name}", 2500)

    def open_profile(self):
        dlg = ProfileDialog(self)
        dlg.exec()

    def apply_theme(self):
        app = QtWidgets.QApplication.instance()
        if not app:
            return

        setup_app_theme(app, self.current_theme)
        self.top_bar.update_theme_button(self.current_theme)
        self.force_style_update()

        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Тема: {self.current_theme}", 2000)

    def force_style_update(self):
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
        self.current_theme = self.theme_manager.toggle_theme()
        self.apply_theme()


def main():
    app = QtWidgets.QApplication(sys.argv)
    setup_app_theme(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()