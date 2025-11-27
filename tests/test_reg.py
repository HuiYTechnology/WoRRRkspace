import flet as ft
try:
    from tests import config as cfg
    from tests.splash_screen import SplashScreen
except Exception:
    import config as cfg
    from splash_screen import SplashScreen

class RegApp:
    def __init__(self):
        self.users_db = {
            "user@example.com": "password123",
            "test@test.com": "test123"
        }
    
    async def main(self, page: ft.Page):
        page.title = "WoRRRkspace Auth - Register"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 0
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        # Установка размера окна для регистрации
        self.set_window_size(page, cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT_REGISTER)
        
        self.page = page
        
        # Показываем заставку
        splash = SplashScreen(page)
        await splash.show()
        
        # Переходим к основной форме
        self.create_auth_ui()
    
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
        
    def create_auth_ui(self):
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
        
        self.register_form = ft.Container(
            content=self.create_register_form(),
            width=cfg.PANEL_WIDTH,
        )
        
        auth_container = ft.Container(
            content=ft.Column([
                ft.Row([theme_toggle], alignment=ft.MainAxisAlignment.END),
                logo,
                self.register_form
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
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
    
    def create_register_form(self) -> ft.Column:
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
        
        return ft.Column([
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
                "Уже есть аккаунт? Войдите",
                on_click=lambda _: self.show_snackbar("Используй test_auth.py для входа")
            )
        ])
    
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
    
    def register(self, e):
        email = self.register_email.value
        password = self.register_password.value
        confirm_password = self.register_confirm_password.value
        
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
        self.register_email.value = ""
        self.register_password.value = ""
        self.register_confirm_password.value = ""
        self.page.update()
    
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
    app = RegApp()
    await app.main(page)

if __name__ == "__main__":
    ft.app(target=main)