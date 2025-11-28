"""Переделать когда бд будет готова"""

import sys
import os
import warnings
import subprocess
import platform
import shutil
import winreg
from pathlib import Path

# Подавляем DeprecationWarning от SIP
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

from PyQt6 import QtWidgets, QtCore

DEFAULT_ENV_PATH = "db\.env"


try:
    from ..src.python.theme_util import SystemThemeDetector
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: добавляем путь вручную для отладки
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    src_python_path = project_root / "worrrkspace" / "src" / "python"
    print(f"Trying to add path: {src_python_path}")
    sys.path.insert(0, str(src_python_path))
    from theme_util import SystemThemeDetector

# Замените функцию setup_dark_theme() на:
def setup_app_theme():
    """Настраивает тему приложения в соответствии с системной"""
    SystemThemeDetector.apply_system_theme(QtWidgets.QApplication.instance())


# -----------------------------------------------------------------------------
# Worker для проверки готовности PostgreSQL в отдельном потоке
# -----------------------------------------------------------------------------

# class PgReadyWorker(QtCore.QObject):



# -----------------------------------------------------------------------------
# Утилиты для работы с PostgreSQL
# -----------------------------------------------------------------------------
class PostgresUtils:
    @staticmethod
    def find_psql_executable():
        """Ищет исполняемый файл psql в системе"""
        # 1. Проверяем PATH
        psql_path = shutil.which("psql")
        if psql_path:
            return psql_path

        # 2. Для Windows: проверяем реестр и стандартные пути
        if platform.system() == "Windows":
            psql_path = PostgresUtils._find_psql_windows()
            if psql_path:
                return psql_path

        # 3. Для Linux/Mac: проверяем стандартные пути
        else:
            psql_path = PostgresUtils._find_psql_unix()
            if psql_path:
                return psql_path

        return None

    @staticmethod
    def _find_psql_windows():
        """Ищет psql в Windows через реестр и стандартные пути"""
        # Проверяем реестр на наличие установленного PostgreSQL
        try:
            # PostgreSQL в реестре
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PostgreSQL\Installations"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PostgreSQL"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PostgreSQL"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\PostgreSQL\Installations"),
            ]

            for hive, path in reg_paths:
                try:
                    with winreg.OpenKey(hive, path) as key:
                        try:
                            i = 0
                            while True:
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, subkey_name) as subkey:
                                        try:
                                            install_path, _ = winreg.QueryValueEx(subkey, "Base Directory")
                                            if install_path:
                                                psql_path = os.path.join(install_path, "bin", "psql.exe")
                                                if os.path.exists(psql_path):
                                                    return psql_path
                                        except FileNotFoundError:
                                            pass
                                except OSError:
                                    break
                                i += 1
                        except OSError:
                            pass
                except FileNotFoundError:
                    continue
        except Exception:
            pass

        # Проверяем стандартные пути установки
        standard_paths = [
            # Program Files
            r"C:\Program Files\PostgreSQL\*\bin\psql.exe",
            r"C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe",
            # Прямые пути к распространенным версиям
            r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\12\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\11\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\10\bin\psql.exe",
            # Для OpenServer и других сборок
            r"C:\OpenServer\modules\database\PostgreSQL-*\bin\psql.exe",
            r"C:\OSPanel\modules\database\PostgreSQL-*\bin\psql.exe",
            # Пользовательские установки
            os.path.expanduser(r"~\PostgreSQL\*\bin\psql.exe"),
        ]

        for path_pattern in standard_paths:
            matches = list(Path("C:\\").glob(path_pattern))
            if matches:
                return str(matches[0])

        return None

    @staticmethod
    def _find_psql_unix():
        """Ищет psql в Linux/Mac через стандартные пути"""
        unix_paths = [
            "/usr/bin/psql",
            "/usr/local/bin/psql",
            "/opt/local/bin/psql",
            "/usr/lib/postgresql/*/bin/psql",
            "/opt/postgresql/bin/psql",
            "/Applications/Postgres.app/Contents/Versions/*/bin/psql",  # Mac
            # Homebrew на Mac
            "/usr/local/opt/postgresql@*/bin/psql",
            "/usr/local/opt/postgresql/bin/psql",
            # Linux package managers
            "/var/lib/pgsql/bin/psql",
        ]

        for path_pattern in unix_paths:
            matches = list(Path("/").glob(path_pattern))
            if matches:
                return str(matches[0])

        return None

    @staticmethod
    def is_postgres_installed():
        """Проверяет, установлен ли PostgreSQL в системе"""
        # 1. Проверяем наличие psql
        if PostgresUtils.find_psql_executable():
            return True

        # 2. Проверяем службы PostgreSQL (Windows)
        if platform.system() == "Windows":
            if PostgresUtils._check_windows_services():
                return True

        # 3. Проверяем процессы PostgreSQL
        if PostgresUtils._check_postgres_processes():
            return True

        # 4. Проверяем порт 5432
        if PostgresUtils._check_postgres_port():
            return True

        return False

    @staticmethod
    def _check_windows_services():
        """Проверяет службы PostgreSQL в Windows"""
        try:
            # Ищем службы с postgres в имени
            service_names = [
                "postgresql",
                "pgsql",
                "postgres",
                "PostgreSQL"
            ]

            for service_name in service_names:
                try:
                    result = subprocess.run(
                        ["sc", "query", service_name],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and ("RUNNING" in result.stdout or "STOPPED" in result.stdout):
                        return True
                except:
                    continue

            # Альтернативный способ через Get-Service (PowerShell)
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-Service | Where-Object {$_.Name -like '*postgres*' -or $_.DisplayName -like '*PostgreSQL*'}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except:
                pass

        except Exception:
            pass

        return False

    @staticmethod
    def _check_postgres_processes():
        """Проверяет запущенные процессы PostgreSQL"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq postgres.exe"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return "postgres.exe" in result.stdout
            else:
                # Linux/Mac
                result = subprocess.run(
                    ["pgrep", "-x", "postgres"],
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
        except:
            return False

    @staticmethod
    def _check_postgres_port():
        """Проверяет, слушает ли PostgreSQL порт 5432"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 5432))
            sock.close()
            return result == 0
        except:
            return False

    @staticmethod
    def get_psql_version():
        """Получает версию PostgreSQL"""
        psql_path = PostgresUtils.find_psql_executable()
        if not psql_path:
            return "PostgreSQL не найден"

        try:
            result = subprocess.run(
                [psql_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "Не удалось определить версию"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    @staticmethod
    def find_postgres_installer():
        """Ищет установщик PostgreSQL в проекте"""
        search_patterns = [
            "resources/installers/postgresql*.exe",
            "resources/installers/postgreSQL*.exe",
            "installers/postgresql*.exe",
            "installers/PostgreSQL*.exe",
            "postgresql_installer.exe",
            "PostgreSQL_installer.exe",
            "setup/postgresql*.exe",
            "database/installers/postgresql*.exe",
            "PostgreSQL*.exe",
            "postgresql*.exe",
        ]

        for pattern in search_patterns:
            matches = list(Path(".").rglob(pattern))
            if matches:
                # Предпочитаем установщики с более полными именами
                full_matches = [m for m in matches if "postgresql" in m.name.lower() and "setup" in m.name.lower()]
                if full_matches:
                    return str(full_matches[0])
                return str(matches[0])

        return None

    @staticmethod
    def install_postgres():
        """Запускает установщик PostgreSQL"""
        installer_path = PostgresUtils.find_postgres_installer()

        if not installer_path:
            return False, "Установщик PostgreSQL не найден в проекте. Разместите установщик в папке installers/"

        try:
            if platform.system() == "Windows":
                # Запускаем установщик
                subprocess.Popen([installer_path], shell=True)
                return True, f"Установщик PostgreSQL запущен: {os.path.basename(installer_path)}"
            else:
                return False, "Автоматическая установка поддерживается только в Windows"
        except Exception as e:
            return False, f"Ошибка при запуске установщика: {str(e)}"


# -----------------------------------------------------------------------------
# Главный выбор: локальная или удалённая БД
# -----------------------------------------------------------------------------
class FirstRunDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Первый запуск — настройка БД")
        self.setMinimumSize(500, 280)
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QtWidgets.QLabel("Настройка базы данных")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title_label)

        label = QtWidgets.QLabel(
            "Выберите режим работы приложения:\n"
            "• Локальная база данных (PostgreSQL установится и создастся автоматически)\n"
            "• Удалённая база данных (вы укажете параметры подключения вручную)"
        )
        label.setWordWrap(True)
        label.setStyleSheet("padding: 10px; border-radius: 5px;")
        layout.addWidget(label)

        # Группа радиокнопок
        radio_group = QtWidgets.QGroupBox("Режим работы")
        radio_layout = QtWidgets.QVBoxLayout(radio_group)
        radio_layout.setSpacing(10)

        self.radio_local = QtWidgets.QRadioButton("Локальная база данных")
        self.radio_remote = QtWidgets.QRadioButton("Удалённая база данных")
        self.radio_local.setChecked(True)

        # Увеличим размер шрифта для радиокнопок
        font = self.radio_local.font()
        font.setPointSize(11)
        self.radio_local.setFont(font)
        self.radio_remote.setFont(font)

        radio_layout.addWidget(self.radio_local)
        radio_layout.addWidget(self.radio_remote)

        layout.addWidget(radio_group)

        # Кнопка далее
        btn_next = QtWidgets.QPushButton("Далее →")
        btn_next.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
        """)
        btn_next.clicked.connect(self.on_next)
        layout.addWidget(btn_next)

    def on_next(self):
        if self.radio_local.isChecked():
            dlg = LocalSetupDialog(self)
            dlg.exec()
        else:
            dlg = RemoteSetupDialog(self)
            dlg.exec()
        self.accept()


# -----------------------------------------------------------------------------
# Диалог настройки локальной БД
# -----------------------------------------------------------------------------
class LocalSetupDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Локальная установка PostgreSQL")
        self.setMinimumSize(700, 550)
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DriveHDIcon))

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Информационная панель
        self.info = QtWidgets.QLabel(
            "Эта процедура создаст локальную установку PostgreSQL и базу данных приложения.\n"
            "Выполняйте действия по порядку: проверка → установка → создание БД."
        )
        self.info.setWordWrap(True)
        self.info.setStyleSheet("""
            QLabel { 
                padding: 12px; 
                border-radius: 5px;
                border-left: 4px solid #2a82da;
            }
        """)
        layout.addWidget(self.info)

        # Лог-панель
        log_group = QtWidgets.QGroupBox("Журнал операций")
        log_layout = QtWidgets.QVBoxLayout(log_group)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: 'Consolas', 'Monospace'; font-size: 10pt;")
        log_layout.addWidget(self.log)

        layout.addWidget(log_group, stretch=1)

        # Панель кнопок
        btn_group = QtWidgets.QGroupBox("Действия")
        btn_layout = QtWidgets.QHBoxLayout(btn_group)

        self.btn_check = QtWidgets.QPushButton("Проверить PostgreSQL")
        self.btn_check.clicked.connect(self.check_postgres)

        self.btn_install = QtWidgets.QPushButton("Установить PostgreSQL")
        self.btn_install.clicked.connect(self.install_postgres)

        self.btn_create = QtWidgets.QPushButton("Создать БД приложения")
        self.btn_create.clicked.connect(self.create_db_user)

        btn_layout.addWidget(self.btn_check)
        btn_layout.addWidget(self.btn_install)
        btn_layout.addWidget(self.btn_create)

        layout.addWidget(btn_group)

        # Переменные для управления потоками
        self.ready_thread = None
        self.ready_worker = None

    def append(self, text: str):
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log.appendPlainText(f"[{timestamp}] {text}")
        # Автопрокрутка к новому тексту
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        QtWidgets.QApplication.processEvents()

    def check_postgres(self):
        self.append("Проверка наличия PostgreSQL...")

        # Детальная проверка разными методами
        psql_path = PostgresUtils.find_psql_executable()
        if psql_path:
            self.append(f"✅ Найден psql: {psql_path}")
            version = PostgresUtils.get_psql_version()
            self.append(f"Версия: {version}")
        else:
            self.append("❌ psql не найден в системе")

        # Проверка служб
        if platform.system() == "Windows":
            if PostgresUtils._check_windows_services():
                self.append("✅ Обнаружены службы PostgreSQL")
            else:
                self.append("❌ Службы PostgreSQL не найдены")

        # Проверка процессов
        if PostgresUtils._check_postgres_processes():
            self.append("✅ Обнаружены процессы PostgreSQL")
        else:
            self.append("❌ Процессы PostgreSQL не найдены")

        # Проверка порта
        if PostgresUtils._check_postgres_port():
            self.append("✅ PostgreSQL слушает порт 5432")
        else:
            self.append("❌ PostgreSQL не слушает порт 5432")

        # Итог - запускаем проверку готовности в отдельном потоке
        if PostgresUtils.is_postgres_installed():
            self.append("✅ PostgreSQL установлен в системе")
            self.start_ready_check()
        else:
            self.append("❌ PostgreSQL не найден. Можно установить автоматически.")

    def start_ready_check(self):
        """Запускает проверку готовности PostgreSQL в отдельном потоке"""
        self.append("Запуск проверки готовности PostgreSQL...")

        # Отключаем кнопки на время проверки
        # self.btn_check.setEnabled(False)
        # self.btn_install.setEnabled(False)
        # self.btn_create.setEnabled(False)

        # Создаем поток и worker
        # self.ready_thread = QtCore.QThread()
        # self.ready_worker = PgReadyWorker(timeout=10)
        # self.ready_worker.moveToThread(self.ready_thread)
        #
        # Подключаем сигналы
        # self.ready_thread.started.connect(self.ready_worker.run)
        # self.ready_worker.progress.connect(self.append)
        # self.ready_worker.finished.connect(self.on_ready_check_finished)
        # self.ready_worker.finished.connect(self.ready_thread.quit)
        # self.ready_worker.finished.connect(self.ready_worker.deleteLater)
        # self.ready_thread.finished.connect(self.ready_thread.deleteLater)
        # self.ready_thread.finished.connect(self.on_ready_thread_finished)

        # Запускаем поток
        # self.ready_thread.start()

    def on_ready_check_finished(self, is_ready: bool, message: str):
        """Обрабатывает завершение проверки готовности"""
        self.append(message)
        if is_ready:
            self.append("Состояние PostgreSQL: готов")
        else:
            self.append("Состояние PostgreSQL: не готов")

    def on_ready_thread_finished(self):
        """Обрабатывает завершение потока"""
        # Включаем кнопки обратно
        self.btn_check.setEnabled(True)
        self.btn_install.setEnabled(True)
        self.btn_create.setEnabled(True)

        # Очищаем ссылки
        # self.ready_thread = None
        # self.ready_worker = None

    def install_postgres(self):
        self.append("Попытка автоматической установки PostgreSQL...")
        ok, msg = PostgresUtils.install_postgres()
        self.append(msg)
        if ok:
            self.append("Ожидание завершения установки...")
            QtWidgets.QMessageBox.information(
                self,
                "Установка запущена",
                "Установщик PostgreSQL запущен. Дождитесь завершения установки и нажмите 'Проверить PostgreSQL' для подтверждения."
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Ошибка установки", "Автоматическая установка не удалась.\n" + msg
            )

    def create_db_user(self):
        dlg = CreateDBUserDialog(self)
        # if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        #     params = dlg.result_params
        #     self.append("Создание пользователя и базы данных...")
        #
        #     db_dir = os.path.join(os.path.dirname(__file__), "database")
        #     candidates = [
        #         os.path.join(db_dir, "init.sql"),
        #         os.path.join(db_dir, "DB_worrrkspace.txt"),
        #         os.path.join(db_dir, "schema.sql"),
        #     ]
        #     script_path = next((p for p in candidates if os.path.exists(p)), None)
        #     if not script_path:
        #         QtWidgets.QMessageBox.warning(
        #             self,
        #             "Файл не найден",
        #             f"В каталоге {db_dir} не найден SQL-скрипт базы данных.",
        #         )
        #         return
        #
        #     self.append(f"Используется скрипт: {os.path.basename(script_path)}")

            # ok, msg = foo(
            #     superuser_connect_params=params["super"],
            #     new_db=params["db_name"],
            #     new_user=params["db_user"],
            #     new_password=params["db_password"],
            #     script_path=script_path,
            # )
            # self.append(msg)
            # if ok:
            #     env = {
            #         "DB_HOST": params["super"].get("host", "localhost"),
            #         "DB_PORT": params["super"].get("port", 5432),
            #         "DB_NAME": params["db_name"],
            #         "DB_USER": params["db_user"],
            #         "DB_PASSWORD": params["db_password"],
            #         "DB_MIN_CONN": "1",
            #         "DB_MAX_CONN": "10",
            #         "DB_INIT_POOL": "1",
            #     }
            #     # write_env(DEFAULT_ENV_PATH, env)
            #     # write_env_example()
            #     self.append(f"💾 Файл .env сохранён в {DEFAULT_ENV_PATH}")
            #     QtWidgets.QMessageBox.information(
            #         self, "Готово", "Локальная БД создана и инициализирована успешно."
            #     )
            # else:
            #     QtWidgets.QMessageBox.critical(self, "Ошибка", msg)


# -----------------------------------------------------------------------------
# Диалог ввода параметров для создания БД
# -----------------------------------------------------------------------------
class CreateDBUserDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры новой базы данных")
        self.setMinimumSize(500, 400)
        self.result_params = {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Группа суперпользователя
        su_group = QtWidgets.QGroupBox("Подключение суперпользователя")
        su_layout = QtWidgets.QFormLayout(su_group)
        su_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.su_host = QtWidgets.QLineEdit("localhost")
        self.su_port = QtWidgets.QLineEdit("5432")
        self.su_user = QtWidgets.QLineEdit("postgres")
        self.su_password = QtWidgets.QLineEdit()
        self.su_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        su_layout.addRow("Хост:", self.su_host)
        su_layout.addRow("Порт:", self.su_port)
        su_layout.addRow("Пользователь:", self.su_user)
        su_layout.addRow("Пароль:", self.su_password)

        layout.addWidget(su_group)

        # Группа новой БД
        db_group = QtWidgets.QGroupBox("Новая база данных")
        db_layout = QtWidgets.QFormLayout(db_group)
        db_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.db_name = QtWidgets.QLineEdit("worrrkspace")
        self.db_user = QtWidgets.QLineEdit("worrrkspace_user")
        self.db_password = QtWidgets.QLineEdit()
        self.db_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        db_layout.addRow("Имя БД:", self.db_name)
        db_layout.addRow("Пользователь:", self.db_user)
        db_layout.addRow("Пароль:", self.db_password)

        layout.addWidget(db_group)

        # Кнопки
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def on_ok(self):
        self.result_params = {
            "super": {
                "host": self.su_host.text().strip(),
                "port": int(self.su_port.text().strip() or 5432),
                "user": self.su_user.text().strip(),
                "password": self.su_password.text().strip() or None,
                "dbname": "postgres",
            },
            "db_name": self.db_name.text().strip(),
            "db_user": self.db_user.text().strip(),
            "db_password": self.db_password.text().strip(),
        }
        self.accept()


# -----------------------------------------------------------------------------
# Диалог для удалённого подключения
# -----------------------------------------------------------------------------
class RemoteSetupDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к удалённой БД")
        self.setMinimumSize(500, 350)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Группа параметров подключения
        conn_group = QtWidgets.QGroupBox("Параметры подключения")
        conn_layout = QtWidgets.QFormLayout(conn_group)
        conn_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.host = QtWidgets.QLineEdit("db.example.com")
        self.port = QtWidgets.QLineEdit("5432")
        self.dbname = QtWidgets.QLineEdit("worrrkspace")
        self.user = QtWidgets.QLineEdit("worrrkspace_user")
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        conn_layout.addRow("Хост:", self.host)
        conn_layout.addRow("Порт:", self.port)
        conn_layout.addRow("Имя БД:", self.dbname)
        conn_layout.addRow("Пользователь:", self.user)
        conn_layout.addRow("Пароль:", self.password)

        layout.addWidget(conn_group)

        # Информационная панель
        info_label = QtWidgets.QLabel(
            "Убедитесь, что:\n"
            "• База данных уже создана на удалённом сервере\n"
            "• Пользователь имеет необходимые права\n"
            "• Сервер доступен с данного компьютера"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #404040;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #ffa500;
            }
        """)
        layout.addWidget(info_label)

        # Кнопки
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def on_ok(self):
        env = {
            "DB_HOST": self.host.text().strip(),
            "DB_PORT": self.port.text().strip() or "5432",
            "DB_NAME": self.dbname.text().strip(),
            "DB_USER": self.user.text().strip(),
            "DB_PASSWORD": self.password.text().strip(),
            "DB_MIN_CONN": "1",
            "DB_MAX_CONN": "10",
            "DB_INIT_POOL": "1",
        }
        # write_env(DEFAULT_ENV_PATH, env)
        # write_env_example()
        QtWidgets.QMessageBox.information(
            self, "Готово", f"Параметры подключения сохранены в {DEFAULT_ENV_PATH}"
        )
        self.accept()


# -----------------------------------------------------------------------------
# Точка входа
# -----------------------------------------------------------------------------
def run_first_run():
    app = QtWidgets.QApplication(sys.argv)
    setup_app_theme()  # вместо setup_dark_theme()
    dlg = FirstRunDialog()
    dlg.exec()
    sys.exit(0)


if __name__ == "__main__":
    run_first_run()