import flet as ft
import asyncio
try:
    from tests import config as cfg
except Exception:
    import config as cfg

class SplashScreen:
    def __init__(self, page: ft.Page):
        self.page = page
    
    async def show(self):
        """Показать заставку и вернуть управление через заданное время"""
        splash_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.WORKSPACE_PREMIUM, 
                        size=120, 
                        color=cfg.SPLASH_TEXT_COLOR
                    ),
                    ft.Container(height=40),
                    ft.Text(
                        "WoRRRkspace",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=cfg.SPLASH_TEXT_COLOR
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "Version 1.0",
                        size=16,
                        color=cfg.SPLASH_TEXT_COLOR
                    ),
                    ft.Container(height=60),
                    ft.Container(
                        content=ft.ProgressBar(),
                        width=200,
                        height=4
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            bgcolor=cfg.SPLASH_BG_COLOR,
            alignment=ft.alignment.center,
        )
        
        self.page.clean()
        self.page.add(splash_container)
        self.page.update()
        
        # Ждем указанное время
        await asyncio.sleep(cfg.SPLASH_DURATION / 1000)