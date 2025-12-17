"""Добавить инициализацию бд"""

import os
import sys
import subprocess
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def check_dlls_exist():
    """Проверяет наличие скомпилированных DLL файлов"""
    dll_paths = [
        Path("worrrkspace/src/cpp_logger/lib/logger.dll"),
        Path("worrrkspace/src/cpp_calculate/lib/calculate.dll")
    ]
    return all(dll.exists() for dll in dll_paths)


def check_env_exists():
    """Проверяет наличие .env файла"""
    env_paths = [
        Path("DataBase/.env"),
        Path(".env")
    ]
    return any(env.exists() for env in env_paths)


def run_build_simple():
    """Запускает сборку C++ компонентов"""
    print("🔨 Запуск сборки C++ компонентов...")
    try:
        result = subprocess.run([sys.executable, "worrrkspace/build_simple.py"],
                                capture_output=True, text=True, timeout=300)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Ошибка сборки: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Ошибка при запуске сборки: {e}")
        return False


def run_first_run():
    """Запускает первоначальную настройку"""
    print("Запуск первоначальной настройки...")
    try:
        result = subprocess.run([sys.executable, "worrrkspace/windows\FirstRunWindow.py"],
                                capture_output=True, text=True, timeout=120)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Ошибка настройки: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Ошибка при запуске настройки: {e}")
        return False


def initialize_database():
    """Инициализирует подключение к базе данных"""
    # TODO: Инициализирует подключение к базе данных


def create_windows_module():
    """Создает папку windows и копирует туда файлы окон, если их нет"""
    windows_dir = Path("worrrkspace/windows")
    if not windows_dir.exists():
        print("Создаем папку windows...")
        windows_dir.mkdir(exist_ok=True)

        # Копируем файлы окон в папку windows
        import shutil
        files_to_copy = ["AuthorizationWindow.py", "RegistrationWindow.py"]
        for file in files_to_copy:
            if Path(file).exists():
                shutil.copy(file, windows_dir / file)
                print(f"Скопирован {file} в папку windows")
            else:
                print(f"Файл {file} не найден")

    # Создаем __init__.py в папке windows
    init_file = windows_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Windows package\n")


def run_authorization():
    """Запускает окно авторизации"""
    print("Запуск окна авторизации...")
    try:
        # Создаем папку windows и копируем файлы
        create_windows_module()

        # Добавляем текущую директорию в путь для импорта
        import sys
        sys.path.append('.')

        # Пробуем импортировать из папки windows
        try:
            from windows.AuthorizationWindow import AuthorizationWindow
            from windows.RegistrationWindow import RegistrationWindow
        except ImportError as e:
            print(f"Не удалось импортировать из windows: {e}")
            print("Пробуем импортировать напрямую...")
            # Пробуем импортировать напрямую
            from windows.AuthorizationWindow import AuthorizationWindow
            from windows.RegistrationWindow import RegistrationWindow

        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # Пробуем импортировать SystemThemeDetector
        try:
            from core.python.theme_util import SystemThemeDetector
        except ImportError:
            print("SystemThemeDetector не найден, используем заглушку")

            # Создаем заглушку
            class SystemThemeDetector:
                @staticmethod
                def get_system_theme():
                    return "light"

                @staticmethod
                def apply_system_theme(app, theme=None):
                    pass

        print("Создаем приложение...")
        app = QApplication(sys.argv)

        print("Применяем системную тему...")
        SystemThemeDetector.apply_system_theme(app)

        print("Создаем окна...")
        # Создаем оба окна
        auth_window = AuthorizationWindow()
        reg_window = RegistrationWindow()

        print("Настраиваем связи между окнами...")

        # Связываем сигналы переключения между окнами
        def show_registration():
            print("Переход к регистрации")
            auth_window.hide()
            reg_window.clear_fields()
            reg_window.show()

        def show_authorization():
            print("Переход к авторизации")
            reg_window.hide()
            auth_window.clear_fields()
            auth_window.show()

        auth_window.registration_requested.connect(show_registration)
        reg_window.authorization_requested.connect(show_authorization)

        # При успешной регистрации переходим к авторизации
        def on_registration_success(username):
            print(f"Успешная регистрация: {username}")
            reg_window.hide()
            auth_window.show()
            auth_window.show_status(f"Аккаунт {username} успешно создан! Теперь выполните вход.", False)
            # Автоматически заполняем логин
            if hasattr(auth_window, 'login_widget'):
                auth_window.login_widget.setText(username)

        reg_window.registration_successful.connect(on_registration_success)

        # При успешном входе переходим к главному приложению
        def on_login_success(username, user_id):
            print(f"Успешный вход: {username} (ID: {user_id})")
            # TODO: Загрузить данные пользователя и перейти к главному окну
            auth_window.hide()
            # Здесь будет переход к главному рабочему пространству
            print("Переход к главному рабочему пространству...")
            # Временно выходим из приложения
            QTimer.singleShot(1000, app.quit)  # Даем время для показа сообщения

        auth_window.login_successful.connect(on_login_success)

        # Обработка ошибок при закрытии окон
        def on_auth_window_closed():
            print("Окно авторизации закрыто")

        def on_reg_window_closed():
            print("Окно регистрации закрыто")

        auth_window.destroyed.connect(on_auth_window_closed)
        reg_window.destroyed.connect(on_reg_window_closed)

        print("Показываем окно авторизации...")
        # Показываем окно авторизации
        auth_window.show()

        print("Запускаем главный цикл приложения...")
        # Запускаем главный цикл приложения
        result = app.exec()
        print(f"Приложение завершено с кодом: {result}")
        return result

    except Exception as e:
        print(f"Критическая ошибка при запуске авторизации: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Основная функция запуска приложения"""
    print("=" * 50)
    print("Запуск WoRRRkspace...")
    print("=" * 50)

    # 1. Проверяем и собираем C++ компоненты если нужно
    print("\n1. Проверка C++ компонентов...")
    if not check_dlls_exist():
        print("C++ компоненты не найдены, запуск сборки...")
        if not run_build_simple():
            print("Не удалось собрать C++ компоненты")
            return 1
        else:
            print("C++ компоненты успешно собраны")
    else:
        print("C++ компоненты найдены")

    # 2. Проверяем настройку БД
    print("\n2. Проверка конфигурации базы данных...")
    if not check_env_exists():
        print(" Файл .env не найден, запуск первоначальной настройки...")
        if not run_first_run():
            print("Не удалось выполнить первоначальную настройку")
            return 1
        else:
            print("Первоначальная настройка завершена")
    else:
        print("Файл .env найден")

    # 3. Инициализируем базу данных
    print("\n3. Инициализация базы данных...")


    # 4. Запускаем окно авторизации
    print("\n4. Запуск интерфейса авторизации...")
    print("Все проверки пройдены!")
    return run_authorization()


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\nПриложение завершено с кодом выхода: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nПриложение прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nКритическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)