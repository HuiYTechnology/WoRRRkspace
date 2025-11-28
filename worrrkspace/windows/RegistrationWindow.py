"""Переделать ебанные иконки. И отдрочить дизайн"""


import os
import sys
import re
import hashlib
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMessageBox, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import (
    pyqtSignal, QSettings, QTimer, QSize, Qt, QPropertyAnimation,
    QEasingCurve, QPoint, QRectF, QSequentialAnimationGroup,
    QParallelAnimationGroup, pyqtProperty
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QPainterPath, QColor, QFont, QPen, QBrush
)

# Импортируем наши кастомные компоненты из AuthorizationWindow. Переделать нахер. Это надо вывести в отдельную утилиту
from AuthorizationWindow import (
    FloatingLabel, ToastNotification, AnimatedButton,
    FloatingLineEdit, PasswordField, LoadingIndicator,
    SystemThemeDetector
)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)


class RegistrationWindow(QWidget):
    authorization_requested = pyqtSignal()
    registration_successful = pyqtSignal(str)  # Передает username

    def __init__(self):
        super().__init__()

        # Window fade-in
        self._win_opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._win_opacity_anim.setDuration(420)
        self._win_opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Load UI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "RegistrationWindow.ui")
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            self._fallback_ui()

        # Hide static labels
        for label_name in ["fullNameLabel", "emailLabel", "loginLabel", "passwordLabel", "confirmPasswordLabel"]:
            if hasattr(self, label_name):
                getattr(self, label_name).hide()

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

        # Вставляем status_label в layout перед кнопкой регистрации
        if hasattr(self, "verticalLayout"):
            idx = self.verticalLayout.indexOf(self.registerButton)
            if idx != -1:
                self.verticalLayout.insertWidget(idx, self.status_label)

        # Подключение
        self.setup_connections()

        QTimer.singleShot(60, self._start_show)

    def _fallback_ui(self):
        self.setWindowTitle("Регистрация")
        self.setFixedSize(440, 580)

        v = QVBoxLayout(self)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(12)

        # Заголовок
        lbl = QLabel("Регистрация")
        lbl.setObjectName("registerLabel")
        lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(lbl)

        v.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Поля ввода (будут заменены на кастомные)
        self.fullNameLine = QLineEdit()
        self.emailLine = QLineEdit()
        self.loginLine = QLineEdit()
        self.passwordLine = QLineEdit()
        self.passwordLine.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmPasswordLine = QLineEdit()
        self.confirmPasswordLine.setEchoMode(QLineEdit.EchoMode.Password)

        # Кнопки
        self.registerButton = QPushButton("Зарегистрироваться")
        self.authorizationLink = QPushButton("Уже есть аккаунт? Войти здесь.")

        # Добавляем в layout
        v.addWidget(self.fullNameLine)
        v.addWidget(self.emailLine)
        v.addWidget(self.loginLine)
        v.addWidget(self.passwordLine)
        v.addWidget(self.confirmPasswordLine)

        v.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        v.addWidget(self.registerButton)
        v.addWidget(self.authorizationLink)

        self.verticalLayout = v

    def _start_show(self):
        """Плавное появление окна"""
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
        for attr in ["fullNameLabel", "emailLabel", "loginLabel", "passwordLabel", "confirmPasswordLabel"]:
            if hasattr(self, attr):
                try:
                    widget = getattr(self, attr)
                    parent_layout.removeWidget(widget)
                    widget.deleteLater()
                    setattr(self, attr, None)
                except:
                    pass

        # Список полей для создания
        fields = [
            ("fullNameLine", "Полное имя", "person", QLineEdit.EchoMode.Normal, "full_name_widget"),
            ("emailLine", "Email", "email", QLineEdit.EchoMode.Normal, "email_widget"),
            ("loginLine", "Логин", "person", QLineEdit.EchoMode.Normal, "login_widget"),
            ("passwordLine", "Пароль", "lock", QLineEdit.EchoMode.Password, "password_widget"),
            ("confirmPasswordLine", "Подтверждение пароля", "lock", QLineEdit.EchoMode.Password,
             "confirm_password_widget")
        ]

        # Находим индексы для вставки
        insert_positions = {}
        for field_name, _, _, _, _ in fields:
            if hasattr(self, field_name):
                try:
                    idx = parent_layout.indexOf(getattr(self, field_name))
                    if idx != -1:
                        insert_positions[field_name] = idx
                except:
                    pass

        # Заменяем поля
        for field_name, placeholder, icon_type, echo_mode, widget_attr in fields:
            if echo_mode == QLineEdit.EchoMode.Password:
                widget = PasswordField(placeholder, theme=self.current_theme)
            else:
                widget = FloatingLineEdit(placeholder, icon_type=icon_type,
                                          theme=self.current_theme, echo_mode=echo_mode)

            widget.setMinimumHeight(48)
            setattr(self, widget_attr, widget)

            if field_name in insert_positions:
                # Заменяем существующее поле
                old_widget = getattr(self, field_name)
                idx = insert_positions[field_name]
                parent_layout.removeWidget(old_widget)
                old_widget.deleteLater()
                parent_layout.insertWidget(idx, widget)
            else:
                # Вставляем новое поле после заголовка
                auth_label_idx = -1
                if hasattr(self, "registerLabel"):
                    try:
                        auth_label_idx = parent_layout.indexOf(self.registerLabel)
                    except:
                        pass

                insert_idx = auth_label_idx + 2 if auth_label_idx != -1 else 1
                parent_layout.insertWidget(insert_idx, widget)

        QTimer.singleShot(100, self._update_floating_labels)

    def _update_floating_labels(self):
        """Обновляем позиции плавающих меток для всех полей"""
        for widget_name in ['full_name_widget', 'email_widget', 'login_widget',
                            'password_widget', 'confirm_password_widget']:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if hasattr(widget, '_update_label_position'):
                    QTimer.singleShot(50, widget._update_label_position)
                elif hasattr(widget, 'floating'):
                    QTimer.singleShot(50, widget.floating._update_label_position)

    def _replace_buttons(self):
        """Заменяем стандартные кнопки на анимированные"""
        if hasattr(self, "registerButton"):
            try:
                idx = self.verticalLayout.indexOf(self.registerButton)
            except:
                idx = -1
            text = self.registerButton.text() if hasattr(self.registerButton, "text") else "Зарегистрироваться"
            self.verticalLayout.removeWidget(self.registerButton)
            self.registerButton.deleteLater()
            btn = AnimatedButton(text)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(
                "QPushButton { border-radius: 10px; padding: 10px 14px; font-weight:600; background-color: #2a82da; color: white; }")
            if idx != -1:
                self.verticalLayout.insertWidget(idx, btn)
            else:
                self.verticalLayout.addWidget(btn)
            self.registerButton = btn

        if hasattr(self, "authorizationLink"):
            try:
                idx = self.verticalLayout.indexOf(self.authorizationLink)
            except:
                idx = -1
            text = self.authorizationLink.text() if hasattr(self.authorizationLink, "text") else "Войти"
            self.verticalLayout.removeWidget(self.authorizationLink)
            self.authorizationLink.deleteLater()
            link_btn = QPushButton(text)
            link_btn.setFlat(True)
            link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            link_btn.setStyleSheet(
                "QPushButton { color: #2a82da; text-decoration: underline; background: transparent; border: none; } QPushButton:hover { color: #0d47a1; }")
            if idx != -1:
                self.verticalLayout.insertWidget(idx, link_btn)
            else:
                self.verticalLayout.addWidget(link_btn)
            self.authorizationLink = link_btn

    def apply_theme(self):
        """Применяем тему ко всем элементам"""
        if self.current_theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

        self._update_inputs_theme()

    def _update_inputs_theme(self):
        """Обновляем тему всех полей ввода"""
        for widget_name in ['full_name_widget', 'email_widget', 'login_widget',
                            'password_widget', 'confirm_password_widget']:
            if hasattr(self, widget_name):
                getattr(self, widget_name).set_theme(self.current_theme)

    def apply_dark_theme(self):
        dark = """
        QWidget { 
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1724, stop:1 #08121a); 
            color: white; 
            font-family: "Segoe UI", Arial; 
            border-radius:12px; 
        }
        QLabel#registerLabel { font-size:26px; font-weight:700; color:#8ad7ff; }
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
        QLabel#registerLabel { font-size:26px; font-weight:700; color:#2a82da; }
        """
        self.setStyleSheet(light)

    def setup_connections(self):
        """Настраиваем соединения сигналов и слотов"""
        self.registerButton.clicked.connect(self.handle_registration)
        if hasattr(self, "authorizationLink"):
            self.authorizationLink.clicked.connect(self.authorization_requested.emit)

        # Подключаем Enter для быстрой отправки формы
        fields = ['full_name_widget', 'email_widget', 'login_widget', 'password_widget', 'confirm_password_widget']
        for field_name in fields:
            if hasattr(self, field_name):
                widget = getattr(self, field_name)
                if hasattr(widget, 'line_edit'):
                    widget.line_edit.returnPressed.connect(self.handle_registration)
                elif hasattr(widget, 'floating') and hasattr(widget.floating, 'line_edit'):
                    widget.floating.line_edit.returnPressed.connect(self.handle_registration)

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

    def validate_email(self, email):
        """Простая валидация email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def hash_password(self, password: str) -> str:
        """Хеширование пароля с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, full_name, email, username, password):
            return None

    def handle_registration(self):
        """Обработка регистрации с валидацией"""
        # Получаем данные из полей
        full_name = self.full_name_widget.text().strip() if hasattr(self, 'full_name_widget') else ""
        email = self.email_widget.text().strip() if hasattr(self, 'email_widget') else ""
        username = self.login_widget.text().strip() if hasattr(self, 'login_widget') else ""
        password = self.password_widget.text() if hasattr(self, 'password_widget') else ""
        confirm_password = self.confirm_password_widget.text() if hasattr(self, 'confirm_password_widget') else ""

        # Валидация полей
        if not full_name:
            self.show_status("Введите полное имя", True)
            self.full_name_widget.shake()
            self.full_name_widget.setFocus()
            return

        if not email:
            self.show_status("Введите электронную почту", True)
            self.email_widget.shake()
            self.email_widget.setFocus()
            return

        if not self.validate_email(email):
            self.show_status("Введите корректный email", True)
            self.email_widget.shake()
            self.email_widget.setFocus()
            return

        # Проверка уникальности email
        """TODO: сделать"""

        if not username:
            self.show_status("Введите логин", True)
            self.login_widget.shake()
            self.login_widget.setFocus()
            return

        if len(username) < 3:
            self.show_status("Логин должен содержать минимум 3 символа", True)
            self.login_widget.shake()
            self.login_widget.setFocus()
            return

        # Проверка уникальности username
        """TODO: сделать"""

        if not password:
            self.show_status("Введите пароль", True)
            self.password_widget.shake()
            self.password_widget.setFocus()
            return

        if len(password) < 12:
            self.show_status("Пароль должен содержать минимум 12 символов", True)
            self.password_widget.shake()
            self.password_widget.setFocus()
            return

        if password != confirm_password:
            self.show_status("Пароли не совпадают", True)
            self.confirm_password_widget.shake()
            self.confirm_password_widget.setFocus()
            return

        # Показываем индикатор загрузки
        self.registerButton.setEnabled(False)
        self.registerButton.setText("Регистрация...")

        # Имитация задержки сети
        QTimer.singleShot(800, lambda: self._perform_registration(full_name, email, username, password))

    def _perform_registration(self, full_name, email, username, password):
        """Выполнение регистрации"""
        try:
            success = self.register_user(full_name, email, username, password)

            self.registerButton.setEnabled(True)
            self.registerButton.setText("Зарегистрироваться")

            if success:
                # Успешная регистрация
                toast = ToastNotification(self, f"Аккаунт {username} успешно создан!", is_success=True)
                toast.show_animated()

                # Fade out окна перед переходом
                fade = QPropertyAnimation(self, b"windowOpacity")
                fade.setDuration(300)
                fade.setStartValue(1.0)
                fade.setEndValue(0.0)
                fade.setEasingCurve(QEasingCurve.Type.OutCubic)
                fade.finished.connect(lambda: self.registration_successful.emit(username))
                fade.start()
            else:
                # Ошибка регистрации
                toast = ToastNotification(self, "Ошибка регистрации. Возможно, пользователь уже существует.",
                                          is_success=False)
                toast.show_animated()

                # Shake анимация для полей
                self.login_widget.shake()
                self.email_widget.shake()

                # Очистка паролей
                self.password_widget.setText("")
                self.confirm_password_widget.setText("")
                self.login_widget.setFocus()

        except ValueError as e:
            # Обрабатываем конкретные ошибки валидации
            self.registerButton.setEnabled(True)
            self.registerButton.setText("Зарегистрироваться")

            error_message = str(e)
            self.show_status(error_message, True)

            # Определяем какое поле нужно выделить
            if "логин" in error_message.lower():
                self.login_widget.shake()
                self.login_widget.setFocus()
            elif "email" in error_message.lower():
                self.email_widget.shake()
                self.email_widget.setFocus()
            else:
                self.login_widget.shake()
                self.email_widget.shake()

            # Очистка паролей
            self.password_widget.setText("")
            self.confirm_password_widget.setText("")

        except Exception as e:
            # Общая ошибка
            self.registerButton.setEnabled(True)
            self.registerButton.setText("Зарегистрироваться")

            self.show_status(f"Ошибка регистрации: {str(e)}", True)
            self.login_widget.shake()
            self.email_widget.shake()

            # Очистка паролей
            self.password_widget.setText("")
            self.confirm_password_widget.setText("")
            self.login_widget.setFocus()

    def toggle_theme(self):
        """Переключение темы"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()

    def clear_fields(self):
        """Очистка всех полей"""
        for widget_name in ['full_name_widget', 'email_widget', 'login_widget',
                            'password_widget', 'confirm_password_widget']:
            if hasattr(self, widget_name):
                getattr(self, widget_name).setText("")

        QTimer.singleShot(50, self._update_floating_labels)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    SystemThemeDetector.apply_system_theme(app)
    w = RegistrationWindow()
    w.show()
    w.authorization_requested.connect(lambda: print("authorization requested"))
    w.registration_successful.connect(lambda u: print("registered:", u))
    sys.exit(app.exec())