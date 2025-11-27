"""Navigation helper for switching between auth screens"""

class Navigator:
    @staticmethod
    def to_login(page, app_instance):
        """Switch to login screen"""
        page.clean()
        app_instance.show_login_form()
    
    @staticmethod
    def to_register(page, app_instance):
        """Switch to register screen"""
        page.clean()
        app_instance.show_register_form()
    
    @staticmethod
    def to_menu(page, app_instance):
        """Switch to menu screen"""
        page.clean()
        app_instance.create_menu_ui()
