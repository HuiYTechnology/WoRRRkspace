"""Переделать кнопку показать пароль. Чуть-чуть переделать анимацию хождения лабле, чтоб не было кривого возвращения плейсхолдера, написать тесты для юи для переадресациами меж окнами. И на свой вкус переделать дизайн."""

import warnings
import hashlib

warnings.filterwarnings("ignore", message=r".*sipPyTypeDict\(\) is deprecated.*", category=DeprecationWarning)

import os
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QWidget, QApplication, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QCheckBox, QSpacerItem
)
from PyQt6.QtCore import (
    pyqtSignal, QSettings, QTimer, QSize, Qt, QPropertyAnimation,
    QEasingCurve, QPoint, QRectF, QSequentialAnimationGroup
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush
)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Попытка импорта SystemThemeDetector
try:
    from src.python.theme_util import SystemThemeDetector
except Exception:
    try:
        from theme_util import SystemThemeDetector
    except Exception:
        class _Dummy:
            @staticmethod
            def get_system_theme(): return "light"

            @staticmethod
            def apply_system_theme(app, theme=None): pass


        SystemThemeDetector = _Dummy()


# ==================== FLOATING LABEL ====================
class FloatingLabel(QLabel):
    def __init__(self, text="", parent=None, theme="light"):
        super().__init__(text, parent)
        self._original_pos = QPoint(0, 0)
        self._target_pos = QPoint(-8, -14)
        self._animation = QPropertyAnimation(self, b"pos")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.theme = theme

        # Устанавливаем тот же шрифт, что и у плейсхолдера
        self._font = QFont()
        self._font.setPointSize(12)  # Тот же размер, что и у QLineEdit

        self._update_style()

        # Устанавливаем высокий z-index чтобы был поверх других элементов
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def set_theme(self, theme):
        self.theme = theme
        self._update_style()

    def _update_style(self):
        if self.theme == "dark":
            self.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent;")
        else:
            self.setStyleSheet("color: rgba(0,0,0,0.7); background: transparent;")
        self.setFont(self._font)

    def set_positions(self, original_pos, target_pos):
        self._original_pos = original_pos
        self._target_pos = target_pos
        self.move(original_pos)

    def animate_to_target(self):
        self.show()
        self.raise_()
        self._animation.setStartValue(self._original_pos)
        self._animation.setEndValue(self._target_pos)
        self._animation.start()

        # Уменьшаем шрифт при подъеме
        small_font = QFont()
        small_font.setPointSize(10)
        self.setFont(small_font)

        if self.theme == "dark":
            self.setStyleSheet("color: rgba(42,130,218,0.95); background: transparent;")
        else:
            self.setStyleSheet("color: rgba(42,130,218,0.95); background: transparent;")

    def animate_to_original(self, on_finished_callback=None):
        # Отключаем предыдущие соединения чтобы избежать множественных вызовов
        try:
            self._animation.finished.disconnect()
        except:
            pass

        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(self._original_pos)

        if on_finished_callback:
            self._animation.finished.connect(on_finished_callback)

        self._animation.finished.connect(self._on_animation_finished)
        self._animation.start()

        # Возвращаем исходный шрифт
        self.setFont(self._font)
        self._update_style()

    def _on_animation_finished(self):
        self.hide()
        try:
            self._animation.finished.disconnect()
        except:
            pass


# ==================== TOAST NOTIFICATION (как в Flet) ====================
class ToastNotification(QWidget):
    """Всплывающее уведомление в стиле"""

    def __init__(self, parent, message, is_success=True, duration=3000):
        super().__init__(parent)
        self.duration = duration
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Setup UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel("✓" if is_success else "✗")
        icon_font = QFont()
        icon_font.setPointSize(18)
        icon_font.setBold(True)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(f"color: {'#4CAF50' if is_success else '#f44336'};")

        # Message
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 11))
        msg_label.setStyleSheet("color: white;")

        layout.addWidget(icon_label)
        layout.addWidget(msg_label, 1)

        # Styling
        bg_color = "#4CAF50" if is_success else "#f44336"
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        # Animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(400)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)

    def show_animated(self):
        """Показать с анимацией"""
        parent = self.parent()
        if parent:
            self.adjustSize()
            # Позиция: сверху по центру
            x = (parent.width() - self.width()) // 2
            y_start = -self.height()
            y_end = 20

            self.move(x, y_start)
            self.show()
            self.raise_()

            # Slide down + fade in
            self.slide_anim.setStartValue(QPoint(x, y_start))
            self.slide_anim.setEndValue(QPoint(x, y_end))
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)

            self.slide_anim.start()
            self.fade_anim.start()

            # Auto hide
            QTimer.singleShot(self.duration, self.hide_animated)

    def hide_animated(self):
        """Скрыть с анимацией"""
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.deleteLater)
        self.fade_anim.start()


# ==================== ANIMATED BUTTON ====================
class AnimatedButton(QPushButton):
    """Кнопка с hover, press и ripple эффектами"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        # Geometry animation
        self._hover_anim = QPropertyAnimation(self, b"geometry")
        self._hover_anim.setDuration(220)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0.0)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(0, 0, 0, 110))
        self.setGraphicsEffect(self._shadow)

        self._blur_anim = QPropertyAnimation(self._shadow, b"blurRadius")
        self._blur_anim.setDuration(200)
        self._blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._use_geom = None
        self._hovered = False

    def showEvent(self, ev):
        use_geom = True
        try:
            parent = self.parent()
            if parent and parent.layout() and parent.layout().indexOf(self) != -1:
                use_geom = False
        except:
            use_geom = False
        self._use_geom = use_geom
        super().showEvent(ev)

    def enterEvent(self, event):
        if self._use_geom:
            rect = self.geometry()
            self._hover_anim.stop()
            self._hover_anim.setStartValue(rect)
            self._hover_anim.setEndValue(rect.adjusted(-3, -3, 3, 3))
            self._hover_anim.start()
        else:
            self._hovered = True
            self._blur_anim.stop()
            self._blur_anim.setStartValue(float(self._shadow.blurRadius()))
            self._blur_anim.setEndValue(12.0)
            self._blur_anim.start()
            self._shadow.setOffset(0, 3)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._use_geom:
            rect = self.geometry()
            self._hover_anim.stop()
            self._hover_anim.setStartValue(rect)
            self._hover_anim.setEndValue(rect.adjusted(3, 3, -3, -3))
            self._hover_anim.start()
        else:
            self._hovered = False
            self._blur_anim.stop()
            self._blur_anim.setStartValue(float(self._shadow.blurRadius()))
            self._blur_anim.setEndValue(0.0)
            self._blur_anim.start()
            self._shadow.setOffset(0, 0)
        super().leaveEvent(event)


# ==================== FLOATING LINE EDIT ====================
class FloatingLineEdit(QWidget):
    """Поле ввода с плавающей меткой и focus-анимацией"""

    def __init__(self, placeholder_text="", icon_type="person", parent=None, echo_mode=QLineEdit.EchoMode.Normal,
                 theme="light"):
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self.icon_type = icon_type
        self.echo_mode = echo_mode
        self.theme = theme
        self._is_label_visible = False
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        self.setMinimumHeight(48)
        self.setMaximumHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Icon
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setPixmap(self._create_icon_pixmap(self.icon_type, 28))
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Line edit с placeholder
        self.line_edit = QLineEdit(self)
        self.line_edit.setEchoMode(self.echo_mode)
        self.line_edit.setPlaceholderText(self.placeholder_text)
        edit_font = QFont()
        edit_font.setPointSize(12)
        self.line_edit.setFont(edit_font)

        # Устанавливаем цвет текста в зависимости от темы
        if self.theme == "dark":
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 12px 6px;
                    background: transparent;
                    color: white;
                }
                QLineEdit::placeholder {
                    color: rgba(255,255,255,0.7);
                }
            """)
        else:
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 12px 6px;
                    background: transparent;
                    color: black;
                }
                QLineEdit::placeholder {
                    color: rgba(0,0,0,0.7);
                }
            """)

        # Floating label - используем тот же шрифт, что и у QLineEdit
        self.floating_label = FloatingLabel(self.placeholder_text, self, self.theme)

        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.line_edit, 1)

        # Events
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.focusInEvent = self._wrap_focus_in(self.line_edit.focusInEvent)
        self.line_edit.focusOutEvent = self._wrap_focus_out(self.line_edit.focusOutEvent)

        # Initial styling
        if self.theme == "dark":
            self.setStyleSheet(
                "QWidget { border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.1); }")
        else:
            self.setStyleSheet(
                "QWidget { border: 1px solid rgba(0,0,0,0.3); border-radius: 8px; background: rgba(0,0,0,0.05); }")

    def _setup_animations(self):
        QTimer.singleShot(100, self._update_label_position)

    def _create_icon_pixmap(self, icon_type: str, size: int) -> QPixmap:
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Выбираем цвет иконки в зависимости от темы
        if self.theme == "dark":
            pen_color = QColor(255, 255, 255)
        else:
            pen_color = QColor(0, 0, 0)

        pen = QPen(pen_color, 2)
        p.setPen(pen)
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        if icon_type == "person":
            p.drawEllipse(int(size * 0.25), int(size * 0.12), int(size * 0.5), int(size * 0.48))
            p.drawArc(int(size * 0.15), int(size * 0.5), int(size * 0.7), int(size * 0.35), 0 * 16, 180 * 16)
        else:
            rect_w, rect_h = int(size * 0.64), int(size * 0.44)
            rect_x, rect_y = int((size - rect_w) / 2), int(size * 0.36)
            p.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, 3, 3)
            p.drawArc(rect_x + int(rect_w * 0.08), int(size * 0.08), int(rect_w * 0.84), int(rect_w * 0.84 * 0.6),
                      0 * 16, 180 * 16)
        p.end()
        return pix

    def _update_label_position(self):
        if not self.isVisible() or self.line_edit.height() == 0:
            QTimer.singleShot(100, self._update_label_position)
            return

        # Получаем позицию относительно текущего виджета
        le_pos = self.line_edit.pos()

        original_pos = QPoint(le_pos.x() + 6, le_pos.y() + (self.line_edit.height() - 20) // 2)
        target_pos = QPoint(le_pos.x() - 8, le_pos.y() - 14)

        self.floating_label.set_positions(original_pos, target_pos)

    def _on_text_changed(self, text):
        # Управляем видимостью placeholder в зависимости от наличия текста и фокуса
        if text:
            self.line_edit.setPlaceholderText("")
            if not self._is_label_visible:
                self.floating_label.animate_to_target()
                self._is_label_visible = True
        else:
            if not self.line_edit.hasFocus():
                # Восстанавливаем placeholder только после завершения анимации
                if self._is_label_visible:
                    self.floating_label.animate_to_original(lambda: self._show_placeholder())
                    self._is_label_visible = False

    def _show_placeholder(self):
        """Показать плейсхолдер после завершения анимации скрытия лейбла"""
        if not self.line_edit.text() and not self.line_edit.hasFocus():
            self.line_edit.setPlaceholderText(self.placeholder_text)

    def _wrap_focus_in(self, original):
        def _focus_in(ev):
            # Всегда скрываем placeholder при фокусе
            self.line_edit.setPlaceholderText("")

            if not self._is_label_visible:
                self.floating_label.animate_to_target()
                self._is_label_visible = True

            if self.theme == "dark":
                self.setStyleSheet(
                    "QWidget { border: 1px solid #2a82da; border-radius: 8px; background: rgba(255,255,255,0.15); }")
            else:
                self.setStyleSheet(
                    "QWidget { border: 1px solid #2a82da; border-radius: 8px; background: rgba(0,0,0,0.08); }")
            original(ev)

        return _focus_in

    def _wrap_focus_out(self, original):
        def _focus_out(ev):
            if not self.line_edit.text():
                if self._is_label_visible:
                    # Запускаем анимацию скрытия и показываем плейсхолдер после ее завершения
                    self.floating_label.animate_to_original(lambda: self._show_placeholder())
                    self._is_label_visible = False

            if self.theme == "dark":
                self.setStyleSheet(
                    "QWidget { border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.1); }")
            else:
                self.setStyleSheet(
                    "QWidget { border: 1px solid rgba(0,0,0,0.3); border-radius: 8px; background: rgba(0,0,0,0.05); }")
            original(ev)

        return _focus_out

    def shake(self):
        """Анимация тряски при ошибке (как в Flet)"""
        original_pos = self.pos()
        shake_anim = QSequentialAnimationGroup(self)

        for offset in [10, -10, 8, -8, 5, -5, 0]:
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(50)
            anim.setEndValue(QPoint(original_pos.x() + offset, original_pos.y()))
            shake_anim.addAnimation(anim)

        shake_anim.start()

    def set_theme(self, theme):
        self.theme = theme
        self.floating_label.set_theme(theme)
        self.icon_label.setPixmap(self._create_icon_pixmap(self.icon_type, 28))

        # Обновляем стили
        if theme == "dark":
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 12px 6px;
                    background: transparent;
                    color: white;
                }
                QLineEdit::placeholder {
                    color: rgba(255,255,255,0.7);
                }
            """)
            self.setStyleSheet(
                "QWidget { border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.1); }")
        else:
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 12px 6px;
                    background: transparent;
                    color: black;
                }
                QLineEdit::placeholder {
                    color: rgba(0,0,0,0.7);
                }
            """)
            self.setStyleSheet(
                "QWidget { border: 1px solid rgba(0,0,0,0.3); border-radius: 8px; background: rgba(0,0,0,0.05); }")

    def text(self):
        return self.line_edit.text()

    def setText(self, txt: str):
        self.line_edit.setText(txt)
        if txt:
            self.floating_label.animate_to_target()
            self._is_label_visible = True
            self.line_edit.setPlaceholderText("")
        else:
            self.floating_label.animate_to_original(lambda: self._show_placeholder())
            self._is_label_visible = False

    def setEchoMode(self, mode):
        self.line_edit.setEchoMode(mode)

    def setFocus(self):
        self.line_edit.setFocus()


# ==================== PASSWORD FIELD ====================
class PasswordField(QWidget):
    def __init__(self, placeholder_text="Пароль", parent=None, theme="light"):
        super().__init__(parent)
        self.theme = theme
        self._setup_ui(placeholder_text)
        QTimer.singleShot(0, lambda: self._ensure_icons())

    def _setup_ui(self, placeholder_text):
        self.setMinimumHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.floating = FloatingLineEdit(placeholder_text, icon_type="lock", echo_mode=QLineEdit.EchoMode.Password, theme=self.theme)
        self.floating.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.toggle_btn = QPushButton(self)
        self.toggle_btn.setFixedSize(36, 36)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFlat(True)

        if self.theme == "dark":
            self.toggle_btn.setStyleSheet("""
                QPushButton { border-radius: 8px; background: rgba(255,255,255,0.1); }
                QPushButton:hover { background: rgba(255,255,255,0.2); }
            """)
        else:
            self.toggle_btn.setStyleSheet("""
                QPushButton { border-radius: 8px; background: rgba(0,0,0,0.05); }
                QPushButton:hover { background: rgba(0,0,0,0.1); }
            """)

        self.toggle_btn.clicked.connect(self.toggle_visibility)

        layout.addWidget(self.floating, 1)
        layout.addWidget(self.toggle_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def _ensure_icons(self):
        self._eye_open_icon = QIcon(self._create_eye_pixmap(18, True))
        self._eye_closed_icon = QIcon(self._create_eye_pixmap(18, False))
        self.toggle_btn.setIcon(self._eye_closed_icon)
        self.toggle_btn.setIconSize(QSize(18, 18))

    def _create_eye_pixmap(self, size: int, open_eye: bool) -> QPixmap:
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Выбираем цвет в зависимости от темы
        if self.theme == "dark":
            pen_color = QColor(255, 255, 255)
            slash_color = QColor(255, 100, 100)
        else:
            pen_color = QColor(0, 0, 0)
            slash_color = QColor(200, 0, 0)

        pen = QPen(pen_color, 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        outer = QRectF(size * 0.08, size * 0.28, size * 0.84, size * 0.44)
        path = QPainterPath()
        path.moveTo(outer.left(), outer.center().y())
        path.arcTo(outer, 180, -180)
        p.drawPath(path)
        pupil = QRectF(size * 0.40, size * 0.36, size * 0.20, size * 0.20)
        p.drawEllipse(pupil)
        if not open_eye:
            slash_pen = QPen(slash_color, 2)
            p.setPen(slash_pen)
            p.drawLine(2, size - 3, size - 3, 2)
        p.end()
        return pix

    def toggle_visibility(self):
        if self.floating.line_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.floating.line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setIcon(self._eye_open_icon)
        else:
            self.floating.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setIcon(self._eye_closed_icon)

    def shake(self):
        """Делегируем shake анимацию"""
        self.floating.shake()

    def set_theme(self, theme):
        self.theme = theme
        self.floating.set_theme(theme)
        self._ensure_icons()

        if theme == "dark":
            self.toggle_btn.setStyleSheet("""
                QPushButton { border-radius: 8px; background: rgba(255,255,255,0.1); }
                QPushButton:hover { background: rgba(255,255,255,0.2); }
            """)
        else:
            self.toggle_btn.setStyleSheet("""
                QPushButton { border-radius: 8px; background: rgba(0,0,0,0.05); }
                QPushButton:hover { background: rgba(0,0,0,0.1); }
            """)

    def text(self):
        return self.floating.line_edit.text()

    def setText(self, txt: str):
        self.floating.setText(txt)

    def setFocus(self):
        self.floating.setFocus()


# ==================== LOADING INDICATOR ====================
class LoadingIndicator(QWidget):
    """Индикатор загрузки"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._angle = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(50)

        # Opacity
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

    def start(self):
        self.opacity_effect.setOpacity(1.0)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.opacity_effect.setOpacity(0.0)

    def _rotate(self):
        self._angle = (self._angle + 15) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.translate(20, 20)
        p.rotate(self._angle)

        pen = QPen(QColor(42, 130, 218), 3)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(-15, -15, 30, 30, 0, 270 * 16)
        p.end()


# ==================== AUTHORIZATION WINDOW ====================
class AuthorizationWindow(QWidget):
    registration_requested = pyqtSignal()
    login_successful = pyqtSignal(str, int)  # Передает username и user_id

    def __init__(self):
        super().__init__()

        # Window fade-in
        self._win_opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._win_opacity_anim.setDuration(420)
        self._win_opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Load UI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "AuthorizationWindow.ui")
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            self._fallback_ui()

        # Hide static labels
        if hasattr(self, "loginLabel"):
            self.loginLabel.hide()
        if hasattr(self, "passwordLabel"):
            self.passwordLabel.hide()

        self.settings = QSettings("YourCompany", "YourApp")

        # Theme
        self.current_theme = SystemThemeDetector.get_system_theme()
        if self.current_theme == "unknown":
            self.current_theme = "light"
        self.apply_theme()

        # Replace inputs & buttons
        self._replace_input_fields()
        self._replace_buttons()

        # Loading indicator
        self.loading = LoadingIndicator(self)
        self.loading.hide()

        # Status label с анимацией
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #f44336; font-size: 11px;")
        self.status_opacity = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(self.status_opacity)
        self.status_opacity.setOpacity(0.0)

        # Вставляем status_label в layout
        if hasattr(self, "verticalLayout"):
            # Найдем индекс кнопки входа и вставим перед ней
            idx = self.verticalLayout.indexOf(self.authorizationButton)
            if idx != -1:
                self.verticalLayout.insertWidget(idx, self.status_label)

        # Подключение
        self.load_saved_credentials()
        self.setup_connections()

        QTimer.singleShot(60, self._start_show)

    def _fallback_ui(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 500)

        v = QVBoxLayout(self)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(12)

        # Заголовок
        lbl = QLabel("Авторизация")
        lbl.setObjectName("authLabel")
        lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(lbl)

        v.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Поля ввода (будут заменены на кастомные)
        self.loginLine = QLineEdit()
        self.passwordLine = QLineEdit()
        self.passwordLine.setEchoMode(QLineEdit.EchoMode.Password)

        # Checkbox "Запомнить меня"
        self.rememberMeCheckBox = QCheckBox("Запомнить меня")

        # Кнопки
        self.authorizationButton = QPushButton("Войти")
        self.registrationWindowLink = QPushButton("Нет аккаунта? Создать здесь.")

        # Добавляем в layout
        v.addWidget(self.loginLine)
        v.addWidget(self.passwordLine)
        v.addWidget(self.rememberMeCheckBox)

        v.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        v.addWidget(self.authorizationButton)
        v.addWidget(self.registrationWindowLink)

        self.verticalLayout = v

    def _start_show(self):
        """Плавное появление окна (как в Flet)"""
        self.setWindowOpacity(0.0)
        self._win_opacity_anim.stop()
        self._win_opacity_anim.setStartValue(0.0)
        self._win_opacity_anim.setEndValue(1.0)
        self._win_opacity_anim.start()
        QTimer.singleShot(100, self._update_floating_labels)

    def _replace_input_fields(self):
        parent_layout = getattr(self, "verticalLayout", None)
        if parent_layout is None:
            return

        # Remove static labels
        for attr in ["loginLabel", "passwordLabel"]:
            if hasattr(self, attr):
                try:
                    widget = getattr(self, attr)
                    parent_layout.removeWidget(widget)
                    widget.deleteLater()
                    setattr(self, attr, None)
                except:
                    pass

        # Login field
        if hasattr(self, "loginLine"):
            try:
                idx = parent_layout.indexOf(self.loginLine)
            except:
                idx = -1
            self.login_widget = FloatingLineEdit("Логин", icon_type="person", theme=self.current_theme)
            self.login_widget.setMinimumHeight(50)
            if idx != -1:
                parent_layout.removeWidget(self.loginLine)
                self.loginLine.deleteLater()
                parent_layout.insertWidget(idx, self.login_widget)
            else:
                parent_layout.insertWidget(1, self.login_widget)
        else:
            self.login_widget = FloatingLineEdit("Логин", icon_type="person", theme=self.current_theme)
            parent_layout.insertWidget(1, self.login_widget)

        # Password field
        if hasattr(self, "passwordLine"):
            try:
                pidx = parent_layout.indexOf(self.passwordLine)
            except:
                pidx = -1
            self.password_widget = PasswordField("Пароль", theme=self.current_theme)
            self.password_widget.setMinimumHeight(50)
            if pidx != -1:
                parent_layout.removeWidget(self.passwordLine)
                self.passwordLine.deleteLater()
                parent_layout.insertWidget(pidx, self.password_widget)
            else:
                login_idx = parent_layout.indexOf(self.login_widget)
                parent_layout.insertWidget(login_idx + 1, self.password_widget)
        else:
            self.password_widget = PasswordField("Пароль", theme=self.current_theme)
            login_idx = parent_layout.indexOf(self.login_widget)
            parent_layout.insertWidget(login_idx + 1, self.password_widget)

        QTimer.singleShot(100, self._update_floating_labels)

    def _update_floating_labels(self):
        if hasattr(self, 'login_widget'):
            self.login_widget._update_label_position()
        if hasattr(self, 'password_widget'):
            self.password_widget.floating._update_label_position()

    def _replace_buttons(self):
        if hasattr(self, "authorizationButton"):
            try:
                idx = self.verticalLayout.indexOf(self.authorizationButton)
            except:
                idx = -1
            text = self.authorizationButton.text() if hasattr(self.authorizationButton, "text") else "Войти"
            self.verticalLayout.removeWidget(self.authorizationButton)
            self.authorizationButton.deleteLater()
            btn = AnimatedButton(text)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(
                "QPushButton { border-radius: 10px; padding: 10px 14px; font-weight:600; background-color: #2a82da; color: white; }")
            if idx != -1:
                self.verticalLayout.insertWidget(idx, btn)
            else:
                self.verticalLayout.addWidget(btn)
            self.authorizationButton = btn

        if hasattr(self, "registrationWindowLink"):
            try:
                idx = self.verticalLayout.indexOf(self.registrationWindowLink)
            except:
                idx = -1
            text = self.registrationWindowLink.text() if hasattr(self.registrationWindowLink, "text") else "Регистрация"
            self.verticalLayout.removeWidget(self.registrationWindowLink)
            self.registrationWindowLink.deleteLater()
            link_btn = QPushButton(text)
            link_btn.setFlat(True)
            link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            link_btn.setStyleSheet(
                "QPushButton { color: #2a82da; text-decoration: underline; background: transparent; border: none; } QPushButton:hover { color: #0d47a1; }")
            if idx != -1:
                self.verticalLayout.insertWidget(idx, link_btn)
            else:
                self.verticalLayout.addWidget(link_btn)
            self.registrationWindowLink = link_btn

    def apply_theme(self):
        if self.current_theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

        # Обновляем тему всех компонентов
        self._update_inputs_theme()

    def _update_inputs_theme(self):
        """Обновляем тему всех полей ввода"""
        if hasattr(self, 'login_widget'):
            self.login_widget.set_theme(self.current_theme)
        if hasattr(self, 'password_widget'):
            self.password_widget.set_theme(self.current_theme)

    def apply_dark_theme(self):
        dark = """
        QWidget { 
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1724, stop:1 #08121a); 
            color: white; 
            font-family: "Segoe UI", Arial; 
            border-radius:12px; 
        }
        QLabel#authLabel { font-size:26px; font-weight:700; color:#8ad7ff; }
        QCheckBox { color: white; font-size: 12px; }
        QCheckBox::indicator { width: 16px; height: 16px; }
        QCheckBox::indicator:unchecked { border: 1px solid rgba(255,255,255,0.5); border-radius: 3px; background: transparent; }
        QCheckBox::indicator:checked { border: 1px solid #2a82da; border-radius: 3px; background: #2a82da; }
        """
        self.setStyleSheet(dark)

    def apply_light_theme(self):
        light = """
        QWidget { 
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #f8fbff, stop:1 #e7f0fb); 
            color: black; 
            font-family: "Segoe UI", Arial; 
            border-radius:12px; 
        }
        QLabel#authLabel { font-size:26px; font-weight:700; color:#2a82da; }
        QCheckBox { color: black; font-size: 12px; }
        QCheckBox::indicator { width: 16px; height: 16px; }
        QCheckBox::indicator:unchecked { border: 1px solid rgba(0,0,0,0.5); border-radius: 3px; background: transparent; }
        QCheckBox::indicator:checked { border: 1px solid #2a82da; border-radius: 3px; background: #2a82da; }
        """
        self.setStyleSheet(light)

    def setup_connections(self):
        self.authorizationButton.clicked.connect(self.handle_login)
        if hasattr(self, "registrationWindowLink"):
            self.registrationWindowLink.clicked.connect(self.registration_requested.emit)
        self.login_widget.line_edit.returnPressed.connect(self.handle_login)
        self.password_widget.floating.line_edit.returnPressed.connect(self.handle_login)

    def load_saved_credentials(self):
        remember_me = self.settings.value("remember_me", False, type=bool)
        saved_username = self.settings.value("username", "")
        if remember_me and saved_username:
            self.login_widget.setText(saved_username)
            try:
                if hasattr(self, "rememberMeCheckBox") and self.rememberMeCheckBox:
                    self.rememberMeCheckBox.setChecked(True)
            except:
                pass

    def save_credentials(self):
        try:
            remember = bool(self.rememberMeCheckBox.isChecked())
        except:
            remember = False
        if remember:
            self.settings.setValue("username", self.login_widget.text())
            self.settings.setValue("remember_me", True)
        else:
            self.settings.remove("username")
            self.settings.setValue("remember_me", False)

    def show_status(self, message, is_error=True):
        """Показать статус с анимацией"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {'#f44336' if is_error else '#4CAF50'}; font-size: 11px;")

        # Fade in animation
        fade_anim = QPropertyAnimation(self.status_opacity, b"opacity")
        fade_anim.setDuration(300)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.start()

        # Auto hide after 3 seconds
        if is_error:
            QTimer.singleShot(3000, self.hide_status)

    def hide_status(self):
        """Скрыть статус с анимацией"""
        fade_anim = QPropertyAnimation(self.status_opacity, b"opacity")
        fade_anim.setDuration(300)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.start()

    def hash_password(self, password: str) -> str:
        """Хеширование пароля с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username, password):
            return None

    def handle_login(self):
        """Обработка входа с анимациями"""
        username = self.login_widget.text().strip()
        password = self.password_widget.text()

        if not username:
            self.show_status("Введите логин", True)
            self.login_widget.shake()
            self.login_widget.setFocus()
            return

        if not password:
            self.show_status("Введите пароль", True)
            self.password_widget.shake()
            self.password_widget.setFocus()
            return

        # Показываем индикатор загрузки
        self.authorizationButton.setEnabled(False)
        self.authorizationButton.setText("Вход...")

        # Имитация задержки сети
        QTimer.singleShot(800, lambda: self._perform_login(username, password))

    def _perform_login(self, username, password):
        """Выполнение входа с реальной аутентификацией"""
        user_data = self.authenticate_user(username, password)

        self.authorizationButton.setEnabled(True)
        self.authorizationButton.setText("Войти")

        if user_data:
            # Успешный вход
            user_id = user_data['user_id']
            username = user_data['username']

            toast = ToastNotification(self, f"С возвращением, {username}!", is_success=True)
            toast.show_animated()

            self.save_credentials()

            # Fade out окна перед переходом
            fade = QPropertyAnimation(self, b"windowOpacity")
            fade.setDuration(300)
            fade.setStartValue(1.0)
            fade.setEndValue(0.0)
            fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade.finished.connect(lambda: self.login_successful.emit(username, user_id))
            fade.start()
        else:
            # Ошибка входа
            toast = ToastNotification(self, "Неверный логин или пароль", is_success=False)
            toast.show_animated()

            # Shake анимация для полей
            self.login_widget.shake()
            self.password_widget.shake()

            # Очистка пароля
            self.password_widget.setText("")
            self.password_widget.setFocus()

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()

    def clear_fields(self):
        self.login_widget.setText("")
        self.password_widget.setText("")
        QTimer.singleShot(50, lambda: self.login_widget._update_label_position())
        QTimer.singleShot(50, lambda: self.password_widget.floating._update_label_position())
        try:
            if self.rememberMeCheckBox:
                self.rememberMeCheckBox.setChecked(False)
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    SystemThemeDetector.apply_system_theme(app)
    w = AuthorizationWindow()
    w.show()
    w.registration_requested.connect(lambda: print("registration requested"))
    w.login_successful.connect(lambda u, i: print("logged in:", u, i))
    sys.exit(app.exec())