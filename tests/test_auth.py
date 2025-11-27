import flet as ft
try:
    from tests import config as cfg
    from tests.splash_screen import SplashScreen
except Exception:
    import config as cfg
    from splash_screen import SplashScreen

class AuthApp:
    def __init__(self):
        self.current_user = None
        self.users_db = {
            "user@example.com": "password123",
            "test@test.com": "test123"
        }
    
    async def main(self, page: ft.Page):
        # Настройка страницы
        page.title = "WoRRRkspace Auth - Login"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 0
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        # Установка размера окна для логина
        self.set_window_size(page, cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT_LOGIN)
        
        self.page = page
        
        # Показываем заставку
        splash = SplashScreen(page)
        await splash.show()
        
        # Переходим к основной форме
        self.show_login_form()
    
    def set_window_size(self, page, width, height):
        """Установка размера окна и центрирование"""
        try:
            page.window.width = width
            page.window.height = height
            page.window.resizable = True
            self.center_window(page)
        except Exception as e:
            print(f"Ошибка при установке размера окна: {e}")
    
    def center_window(self, page):
        """Центрирование окна с обработкой разных версий Flet"""
        try:
            page.window_center()
        except Exception:
            try:
                page.window.center()
            except Exception:
                import threading
                def delayed_center():
                    import time
                    time.sleep(0.1)
                    try:
                        page.window_center()
                        page.update()
                    except Exception:
                        pass
                threading.Thread(target=delayed_center, daemon=True).start()
    
    def show_login_form(self):
        """Показать форму входа"""
        # Устанавливаем размер окна для логина
        self.set_window_size(self.page, cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT_LOGIN)
        
        theme_toggle = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_AUTO,
            on_click=self.toggle_theme,
            tooltip="Системная тема"
        )
        
        logo = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=cfg.ICON_SIZE, color=cfg.PRIMARY_COLOR),
                ft.Text("WoRRRkspace", size=cfg.TITLE_SIZE, weight=ft.FontWeight.BOLD),
                ft.Text("Добро пожаловать!", size=cfg.SUBTITLE_SIZE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(bottom=40)
        )
        
        self.login_email = ft.TextField(
            label="Email",
            hint_text="Введите ваш email",
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
        )
        
        self.login_password = ft.TextField(
            label="Пароль",
            hint_text="Введите ваш пароль",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        
        login_form = ft.Container(
            content=ft.Column([
                ft.Text("Вход в аккаунт", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                self.login_email,
                ft.Container(height=10),
                self.login_password,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Войти",
                    on_click=self.login,
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    width=300
                ),
                ft.Container(height=10),
                ft.TextButton(
                    "Перейти к регистрации",
                    on_click=lambda _: self.show_register_form()
                )
            ]),
            width=cfg.PANEL_WIDTH,
        )
        
        auth_container = ft.Container(
            content=ft.Column([
                ft.Row([theme_toggle], alignment=ft.MainAxisAlignment.END),
                logo,
                login_form
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=cfg.PANEL_PADDING,
            width=cfg.PANEL_WIDTH,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=cfg.SHADOW_COLOR,
                offset=ft.Offset(0, 0),
            )
        )
        
        self.page.clean()
        self.page.add(
            ft.Container(
                content=auth_container,
                width=cfg.PANEL_WIDTH,
                height=cfg.PANEL_HEIGHT_LOGIN,
                alignment=ft.alignment.center,
            )
        )
        self.page.update()

    def show_register_form(self):
        """Показать форму регистрации"""
        # Устанавливаем размер окна для регистрации
        self.set_window_size(self.page, cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT_REGISTER)
        
        theme_toggle = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_AUTO,
            on_click=self.toggle_theme,
            tooltip="Системная тема"
        )
        
        logo = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=cfg.ICON_SIZE, color=cfg.PRIMARY_COLOR),
                ft.Text("WoRRRkspace", size=cfg.TITLE_SIZE, weight=ft.FontWeight.BOLD),
                ft.Text("Присоединяйтесь!", size=cfg.SUBTITLE_SIZE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(bottom=40)
        )
        
        self.register_email = ft.TextField(
            label="Email",
            hint_text="Введите ваш email",
            prefix_icon=ft.Icons.EMAIL,
            border_radius=10,
        )
        
        self.register_password = ft.TextField(
            label="Пароль",
            hint_text="Создайте пароль",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        
        self.register_confirm_password = ft.TextField(
            label="Подтверждение пароля",
            hint_text="Повторите пароль",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        
        register_form = ft.Container(
            content=ft.Column([
                ft.Text("Создание аккаунта", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                self.register_email,
                ft.Container(height=10),
                self.register_password,
                ft.Container(height=10),
                self.register_confirm_password,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Зарегистрироваться",
                    on_click=self.register,
                    style=ft.ButtonStyle(
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    width=300
                ),
                ft.Container(height=10),
                ft.TextButton(
                    "Уже есть аккаунт? Войти",
                    on_click=lambda _: self.show_login_form()
                )
            ]),
            width=cfg.PANEL_WIDTH,
        )
        
        auth_container = ft.Container(
            content=ft.Column([
                ft.Row([theme_toggle], alignment=ft.MainAxisAlignment.END),
                logo,
                register_form
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=cfg.PANEL_PADDING,
            width=cfg.PANEL_WIDTH,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=cfg.SHADOW_COLOR,
                offset=ft.Offset(0, 0),
            )
        )
        
        self.page.clean()
        self.page.add(
            ft.Container(
                content=auth_container,
                width=cfg.PANEL_WIDTH,
                height=cfg.PANEL_HEIGHT_REGISTER,
                alignment=ft.alignment.center,
            )
        )
        self.page.update()
    
    def toggle_theme(self, e):
        if self.page.theme_mode == ft.ThemeMode.SYSTEM:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            e.control.icon = ft.Icons.LIGHT_MODE
            e.control.tooltip = "Светлая тема"
        elif self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            e.control.icon = ft.Icons.DARK_MODE
            e.control.tooltip = "Темная тема"
        else:
            self.page.theme_mode = ft.ThemeMode.SYSTEM
            e.control.icon = ft.Icons.BRIGHTNESS_AUTO
            e.control.tooltip = "Системная тема"
        self.page.update()
    
    def login(self, e):
        email = self.login_email.value
        password = self.login_password.value
        
        if not email or not password:
            self.show_snackbar("Заполните все поля!")
            return
            
        if email in self.users_db and self.users_db[email] == password:
            self.show_snackbar(f"Успешный вход! Добро пожаловать, {email}")
            self.current_user = email
        else:
            self.show_snackbar("Неверный email или пароль!")

    def register(self, e):
        try:
            email = self.register_email.value
            password = self.register_password.value
            confirm_password = self.register_confirm_password.value
        except Exception:
            self.show_snackbar("Ошибка формы регистрации")
            return

        if not email or not password or not confirm_password:
            self.show_snackbar("Заполните все поля!")
            return

        if password != confirm_password:
            self.show_snackbar("Пароли не совпадают!")
            return

        if email in self.users_db:
            self.show_snackbar("Пользователь с таким email уже существует!")
            return

        self.users_db[email] = password
        self.show_snackbar(f"Аккаунт {email} успешно создан!")
        try:
            self.register_email.value = ""
            self.register_password.value = ""
            self.register_confirm_password.value = ""
            self.page.update()
        except Exception:
            pass
    
    def show_snackbar(self, message: str):
        try:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            try:
                self.page.show_snackbar(ft.SnackBar(content=ft.Text(message)))
            except Exception:
                print(message)

async def main(page: ft.Page):
    app = AuthApp()
    await app.main(page)

if __name__ == "__main__":
    ft.app(target=main)