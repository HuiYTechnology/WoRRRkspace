import os
import subprocess
import sys
from pathlib import Path
import shutil
import logging
from datetime import datetime


class ProjectBuilder:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        self.compilers_checked = False
        self.compiler_status = {}

        # Инициализация логгера
        self.setup_logger()

    def setup_logger(self):
        """Настройка Python логгера"""
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Создаем имя файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"build_{timestamp}.log"

        # Настраиваем логгер
        self.logger = logging.getLogger('ProjectBuilder')
        self.logger.setLevel(logging.DEBUG)

        # Форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Обработчик для файла
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Обработчик для консоли (только INFO и выше)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Добавляем обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"Логгер инициализирован. Логи сохраняются в: {log_file}")

    def check_conda_environment(self):
        """Проверяет, активировано ли conda окружение"""
        conda_prefix = os.environ.get('CONDA_PREFIX', '')
        if conda_prefix:
            self.print_warning(f"⚠️  Обнаружено активированное conda окружение: {conda_prefix}")
            self.print_warning("Это может вызвать конфликты с MinGW компилятором")
            self.print_info("Скрипт автоматически исправит окружение для MinGW")
            return True
        return False

    def get_clean_mingw_environment(self):
        """Создает очищенное окружение для MinGW компиляции"""
        env = os.environ.copy()
        
        # Сохраняем важные системные переменные
        system_vars = {
            'PATH': env.get('PATH', ''),
            'TEMP': env.get('TEMP', ''),
            'TMP': env.get('TMP', ''),
            'SystemRoot': env.get('SystemRoot', ''),
            'USERPROFILE': env.get('USERPROFILE', ''),
            'HOMEPATH': env.get('HOMEPATH', ''),
            'USERNAME': env.get('USERNAME', ''),
            'COMPUTERNAME': env.get('COMPUTERNAME', ''),
            'PUBLIC': env.get('PUBLIC', ''),
            'OS': env.get('OS', ''),
            'PROCESSOR_ARCHITECTURE': env.get('PROCESSOR_ARCHITECTURE', ''),
            'NUMBER_OF_PROCESSORS': env.get('NUMBER_OF_PROCESSORS', ''),
            'PROCESSOR_IDENTIFIER': env.get('PROCESSOR_IDENTIFIER', ''),
            'PROCESSOR_LEVEL': env.get('PROCESSOR_LEVEL', ''),
            'PROCESSOR_REVISION': env.get('PROCESSOR_REVISION', ''),
        }
        
        # Удаляем все conda и VS/VC переменные
        keys_to_remove = []
        for key in env.keys():
            key_upper = key.upper()
            if any(x in key_upper for x in ['CONDA', 'VS', 'VC', 'MSVC', 'INCLUDE', 'LIB']):
                # Оставляем только PATH и основные системные переменные
                if key not in system_vars:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            env.pop(key, None)
        
        # Фильтруем PATH: убираем conda пути, оставляем MinGW и системные
        original_path = system_vars['PATH']
        path_parts = original_path.split(';')
        
        # Пути, которые нужно оставить
        allowed_paths = []
        
        # Системные пути Windows
        system_paths = [
            r'C:\Windows\System32',
            r'C:\Windows',
            r'C:\Windows\System32\Wbem',
            r'C:\Windows\System32\WindowsPowerShell\v1.0',
            r'C:\Windows\System32\OpenSSH',
            r'C:\Program Files\Git\cmd',
            r'C:\Program Files\Git\bin',
            r'C:\Program Files\Git\usr\bin',
        ]
        
        # Пути MinGW
        mingw_paths = [
            r'C:\ProgramData\mingw64\mingw64\bin',
            r'C:\msys64\mingw64\bin',
            r'C:\MinGW\bin',
            r'C:\mingw64\bin',
            r'C:\Program Files\mingw-w64\bin',
        ]
        
        # Собираем разрешенные пути
        for path in path_parts:
            path_lower = path.lower()
            # Убираем пути с conda
            if 'conda' in path_lower or 'miniconda' in path_lower or 'anaconda' in path_lower:
                continue
            # Оставляем системные пути и MinGW
            allowed_paths.append(path)
        
        # Добавляем системные пути, если их нет
        for sys_path in system_paths:
            if os.path.exists(sys_path) and sys_path not in allowed_paths:
                allowed_paths.insert(0, sys_path)
        
        # Добавляем MinGW пути, если они существуют
        for mingw_path in mingw_paths:
            if os.path.exists(mingw_path) and mingw_path not in allowed_paths:
                allowed_paths.insert(0, mingw_path)
        
        # Обновляем PATH
        env['PATH'] = ';'.join(allowed_paths)
        
        self.log_debug(f"Очищенное окружение MinGW. Пути PATH: {env['PATH'][:500]}...")
        return env

    def print_header(self, message):
        print(f"\n{'=' * 60}")
        print(f"🔧 {message}")
        print(f"{'=' * 60}")
        self.logger.info(f"=== {message} ===")

    def print_success(self, message):
        print(f"✅ {message}")
        self.logger.info(f"SUCCESS: {message}")

    def print_error(self, message):
        print(f"❌ {message}")
        self.logger.error(f"ERROR: {message}")

    def print_warning(self, message):
        print(f"⚠️ {message}")
        self.logger.warning(f"WARNING: {message}")

    def print_info(self, message):
        print(f"ℹ️ {message}")
        self.logger.info(f"INFO: {message}")

    def log_debug(self, message):
        """Логирование отладочной информации (только в файл)"""
        self.logger.debug(f"DEBUG: {message}")

    def log_exception(self, message):
        """Логирование исключений с полным traceback"""
        self.logger.exception(f"EXCEPTION: {message}")

    def ensure_directories(self):
        """Создает все необходимые директории"""
        self.print_info("Создание структуры директорий...")
        self.log_debug("Начало создания директорий")

        directories = [
            self.project_root / "src" / "cpp_logger" / "lib",
            self.project_root / "src" / "cpp_calculate" / "lib",
            self.project_root / "build_cmake",
            self.project_root / "build_msvc",
            self.project_root / "logs"
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Создана: {directory.relative_to(self.project_root)}")
                self.log_debug(f"Директория создана/уже существует: {directory}")
            except Exception as e:
                self.print_error(f"Ошибка создания директории {directory}: {e}")
                self.log_exception(f"Ошибка создания директории {directory}")

    def check_project_structure(self):
        """Проверяет структуру проекта"""
        self.print_header("ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
        self.log_debug("Начало проверки структуры проекта")

        required_paths = [
            self.project_root / "src" / "cpp" / "logger.cpp",
            self.project_root / "src" / "cpp" / "logger.h",
            self.project_root / "src" / "cpp" / "calculate.cpp",
            self.project_root / "src" / "cpp" / "calculate.h",
            self.project_root / "src" / "cpp" / "CMakeLists.txt",
        ]

        all_exist = True
        for path in required_paths:
            if path.exists():
                self.print_success(f"{path.relative_to(self.project_root)}")
                self.log_debug(f"Файл найден: {path}")
            else:
                self.print_error(f"{path.relative_to(self.project_root)} не найден")
                self.logger.error(f"Файл не найден: {path}")
                all_exist = False

        return all_exist

    def check_compilers(self):
        """Проверяет доступность компиляторов"""
        if self.compilers_checked:
            return self.compiler_status

        self.print_header("ПРОВЕРКА КОМПИЛЯТОРОВ")
        self.log_debug("Начало проверки компиляторов")

        compilers = {
            'MinGW': self._check_mingw,
            'CMake': self._check_cmake,
            'MSVC': self._check_msvc
        }

        self.compiler_status = {}
        for name, checker in compilers.items():
            try:
                self.compiler_status[name] = checker()
                status = "Доступен" if self.compiler_status[name] else "Не доступен"
                self.print_info(f"{name}: {status}")
                self.log_debug(f"Компилятор {name}: {status}")
            except Exception as e:
                self.compiler_status[name] = False
                self.print_error(f"{name}: Ошибка проверки: {e}")
                self.log_exception(f"Ошибка проверки компилятора {name}")

        self.compilers_checked = True
        return self.compiler_status

    def _check_mingw(self):
        """Проверяет доступность MinGW"""
        try:
            self.log_debug("Проверка MinGW...")
            # Используем очищенное окружение для проверки
            env = self.get_clean_mingw_environment()
            result = subprocess.run(['x86_64-w64-mingw32-g++', '--version'],
                                    capture_output=True, text=True, timeout=10,
                                    env=env)
            self.log_debug(f"MinGW check stdout: {result.stdout[:100]}...")
            self.log_debug(f"MinGW check stderr: {result.stderr[:100]}...")
            return result.returncode == 0
        except Exception as e:
            self.log_debug(f"MinGW check exception: {e}")
            return False

    def _check_cmake(self):
        """Проверяет доступность CMake"""
        try:
            self.log_debug("Проверка CMake...")
            result = subprocess.run(['cmake', '--version'],
                                    capture_output=True, text=True, timeout=10)
            self.log_debug(f"CMake check stdout: {result.stdout[:100]}...")
            return result.returncode == 0
        except Exception as e:
            self.log_debug(f"CMake check exception: {e}")
            return False

    def _check_msvc(self):
        """Проверяет доступность MSVC"""
        try:
            self.log_debug("Проверка MSVC...")
            result = subprocess.run(['cl'], capture_output=True, text=True, timeout=10)
            self.log_debug(f"MSVC check stdout: {result.stdout[:100]}...")
            self.log_debug(f"MSVC check stderr: {result.stderr[:100]}...")
            return "Microsoft" in result.stderr or "Microsoft" in result.stdout
        except Exception as e:
            self.log_debug(f"MSVC check exception: {e}")
            return False

    def check_dlls_exist(self):
        """Проверяет существование DLL файлов"""
        self.print_header("ПРОВЕРКА DLL ФАЙЛОВ")
        self.log_debug("Начало проверки DLL файлов")

        required_dlls = [
            self.project_root / "src" / "cpp_logger" / "lib" / "logger.dll",
            self.project_root / "src" / "cpp_calculate" / "lib" / "calculate.dll"
        ]

        all_exist = True
        for dll_path in required_dlls:
            if dll_path.exists():
                file_size = dll_path.stat().st_size
                self.print_success(f"{dll_path.relative_to(self.project_root)} ({file_size} байт)")
                self.log_debug(f"DLL найден: {dll_path} ({file_size} байт)")
            else:
                self.print_error(f"{dll_path.relative_to(self.project_root)} не найден")
                self.logger.error(f"DLL не найден: {dll_path}")
                all_exist = False

        return all_exist

    def build_with_mingw(self):
        """Сборка через MinGW с очищенным окружением"""
        self.print_header("СБОРКА ЧЕРЕЗ MINGW-W64")
        self.log_debug("Начало сборки через MinGW")
        
        # Проверяем conda окружение
        self.check_conda_environment()
        
        # Получаем очищенное окружение для MinGW
        env = self.get_clean_mingw_environment()

        source_dir = self.project_root / "src" / "cpp"
        logger_output = self.project_root / "src" / "cpp_logger" / "lib" / "logger.dll"
        calculate_output = self.project_root / "src" / "cpp_calculate" / "lib" / "calculate.dll"

        success = True

        # Сборка logger.dll
        self.print_info("Компиляция logger.dll...")
        self.log_debug(f"Компиляция logger.dll из {source_dir / 'logger.cpp'}")
        cmd_logger = [
            'x86_64-w64-mingw32-g++',
            '-shared', '-static', '-static-libgcc', '-static-libstdc++',
            '-std=c++17', '-O3',  # Изменено с -O2 на -O3 по заданию
            '-I', str(source_dir),
            str(source_dir / "logger.cpp"),
            '-o', str(logger_output)
        ]

        self.log_debug(f"Команда logger.dll: {' '.join(cmd_logger)}")

        try:
            result = subprocess.run(cmd_logger, capture_output=True, text=True,
                                    cwd=self.project_root, timeout=60, env=env)
            self.log_debug(f"Logger compilation stdout: {result.stdout[:500] if result.stdout else 'Пусто'}")
            self.log_debug(f"Logger compilation stderr: {result.stderr[:500] if result.stderr else 'Пусто'}")

            if result.returncode == 0 and logger_output.exists():
                file_size = logger_output.stat().st_size
                self.print_success(f"logger.dll создан ({file_size} байт)")
                self.log_debug(f"logger.dll успешно создан, размер: {file_size} байт")
            else:
                error_msg = f"Ошибка компиляции logger.dll: returncode={result.returncode}"
                if result.stdout:
                    error_msg += f"\nstdout: {result.stdout[:500]}"
                if result.stderr:
                    error_msg += f"\nstderr: {result.stderr[:500]}"
                self.print_error(error_msg)
                self.logger.error(f"Ошибка компиляции logger.dll: {result.stderr}")
                success = False
        except Exception as e:
            self.print_error(f"Исключение при компиляции logger.dll: {e}")
            self.log_exception(f"Исключение при компиляции logger.dll")
            success = False

        # Сборка calculate.dll
        if success:
            self.print_info("Компиляция calculate.dll...")
            self.log_debug(f"Компиляция calculate.dll из {source_dir / 'calculate.cpp'}")
            cmd_calculate = [
                'x86_64-w64-mingw32-g++',
                '-shared', '-static', '-static-libgcc', '-static-libstdc++',
                '-std=c++17', '-O3',  # Изменено с -O2 на -O3 по заданию
                '-I', str(source_dir),
                str(source_dir / "calculate.cpp"),
                str(source_dir / "logger.cpp"),  # Добавляем logger.cpp как зависимость
                '-o', str(calculate_output)
            ]

            self.log_debug(f"Команда calculate.dll: {' '.join(cmd_calculate)}")

            try:
                result = subprocess.run(cmd_calculate, capture_output=True, text=True,
                                        cwd=self.project_root, timeout=60, env=env)
                self.log_debug(f"Calculate compilation stdout: {result.stdout[:500] if result.stdout else 'Пусто'}")
                self.log_debug(f"Calculate compilation stderr: {result.stderr[:500] if result.stderr else 'Пусто'}")

                if result.returncode == 0 and calculate_output.exists():
                    file_size = calculate_output.stat().st_size
                    self.print_success(f"calculate.dll создан ({file_size} байт)")
                    self.log_debug(f"calculate.dll успешно создан, размер: {file_size} байт")
                else:
                    error_msg = f"Ошибка компиляции calculate.dll: returncode={result.returncode}"
                    if result.stdout:
                        error_msg += f"\nstdout: {result.stdout[:500]}"
                    if result.stderr:
                        error_msg += f"\nstderr: {result.stderr[:500]}"
                    self.print_error(error_msg)
                    self.logger.error(f"Ошибка компиляции calculate.dll: {result.stderr}")
                    success = False
            except Exception as e:
                self.print_error(f"Исключение при компиляции calculate.dll: {e}")
                self.log_exception(f"Исключение при компиляции calculate.dll")
                success = False

        # Копирование зависимостей
        if success:
            self.copy_mingw_dependencies()

        return success

    def copy_mingw_dependencies(self):
        """Копирует зависимости MinGW"""
        self.print_info("Копирование зависимостей MinGW...")
        self.log_debug("Начало копирования зависимостей MinGW")

        # Поиск MinGW
        possible_paths = [
            Path("C:/ProgramData/mingw64/mingw64/bin"),
            Path("C:/msys64/mingw64/bin"),
            Path("C:/MinGW/bin"),
            Path("C:/mingw64/bin"),
            Path("C:/Program Files/mingw-w64/bin"),
        ]

        mingw_bin = None
        for path in possible_paths:
            if path.exists():
                mingw_bin = path
                self.print_success(f"Найден MinGW: {path}")
                self.log_debug(f"MinGW найден: {path}")
                break

        if not mingw_bin:
            self.print_warning("MinGW не найден в стандартных путях")
            self.logger.warning("MinGW не найден в стандартных путях")
            return False

        # Копируем DLL
        required_dlls = [
            "libgcc_s_seh-1.dll",
            "libstdc++-6.dll",
            "libwinpthread-1.dll"
        ]

        target_dirs = [
            self.project_root / "src" / "cpp_calculate" / "lib",
            self.project_root / "src" / "cpp_logger" / "lib"
        ]

        copied_count = 0
        for dll_name in required_dlls:
            source_path = mingw_bin / dll_name
            if not source_path.exists():
                self.print_warning(f"DLL не найдена: {source_path}")
                self.logger.warning(f"DLL не найдена: {source_path}")
                continue

            for target_dir in target_dirs:
                target_path = target_dir / dll_name
                try:
                    shutil.copy2(source_path, target_path)
                    copied_count += 1
                    self.print_success(f"Скопирован: {dll_name} -> {target_path.relative_to(self.project_root)}")
                    self.log_debug(f"DLL скопирована: {dll_name} -> {target_path}")
                except Exception as e:
                    self.print_error(f"Ошибка копирования {dll_name}: {e}")
                    self.log_exception(f"Ошибка копирования {dll_name}")

        if copied_count > 0:
            self.print_success(f"Успешно скопировано {copied_count} файлов")
            self.log_debug(f"Успешно скопировано {copied_count} DLL файлов")
            return True
        else:
            self.print_warning("Не удалось скопировать зависимости")
            self.logger.warning("Не удалось скопировать зависимости MinGW")
            return False

    def build_with_cmake(self):
        """Сборка через CMake"""
        self.print_header("СБОРКА ЧЕРЕЗ CMAKE")
        self.log_debug("Начало сборки через CMake")

        build_dir = self.project_root / "build_cmake"
        build_dir.mkdir(exist_ok=True)

        try:
            # Конфигурация
            self.print_info("Конфигурация CMake...")
            self.log_debug("Конфигурация CMake...")
            
            # Используем генератор MinGW, если доступен
            cmd_configure = ['cmake', '-B', str(build_dir), '-S', str(self.project_root)]
            
            # Пробуем использовать MinGW генератор
            if self.compiler_status.get('MinGW', False):
                cmd_configure.extend(['-G', 'MinGW Makefiles'])
                self.print_info("Используем генератор MinGW Makefiles")
            
            cmd_configure.extend(['-DCMAKE_BUILD_TYPE=Release'])
            
            self.log_debug(f"CMake configure command: {' '.join(cmd_configure)}")

            result = subprocess.run(cmd_configure, capture_output=True, text=True,
                                    cwd=self.project_root, timeout=120)
            self.log_debug(f"CMake configure stdout: {result.stdout[:500] if result.stdout else 'Пусто'}")
            self.log_debug(f"CMake configure stderr: {result.stderr[:500] if result.stderr else 'Пусто'}")

            if result.returncode != 0:
                self.print_error(f"Ошибка конфигурации CMake: {result.stderr}")
                self.logger.error(f"Ошибка конфигурации CMake: {result.stderr}")
                return False

            # Сборка
            self.print_info("Сборка проекта...")
            self.log_debug("Сборка CMake...")
            cmd_build = ['cmake', '--build', str(build_dir), '--config', 'Release']

            self.log_debug(f"CMake build command: {' '.join(cmd_build)}")

            result = subprocess.run(cmd_build, capture_output=True, text=True,
                                    cwd=self.project_root, timeout=180)
            self.log_debug(f"CMake build stdout: {result.stdout[:500] if result.stdout else 'Пусто'}")
            self.log_debug(f"CMake build stderr: {result.stderr[:500] if result.stderr else 'Пусто'}")

            if result.returncode != 0:
                self.print_error(f"Ошибка сборки CMake: {result.stderr}")
                self.logger.error(f"Ошибка сборки CMake: {result.stderr}")
                return False

            # Копирование DLL
            return self.copy_cmake_dlls(build_dir)

        except Exception as e:
            self.print_error(f"Исключение при сборке CMake: {e}")
            self.log_exception(f"Исключение при сборке CMake")
            return False

    def copy_cmake_dlls(self, build_dir):
        """Копирует DLL из CMake сборки"""
        self.print_info("Поиск DLL в сборке CMake...")
        self.log_debug(f"Поиск DLL в {build_dir}")

        success = True

        # Ищем и копируем logger.dll
        logger_dll_files = list(build_dir.rglob("logger.dll"))
        if logger_dll_files:
            source_dll = logger_dll_files[0]
            target_dll = self.project_root / "src" / "cpp_logger" / "lib" / "logger.dll"
            try:
                shutil.copy2(source_dll, target_dll)
                file_size = target_dll.stat().st_size
                self.print_success(f"logger.dll скопирован ({file_size} байт)")
                self.log_debug(f"logger.dll скопирован из {source_dll}")
            except Exception as e:
                self.print_error(f"Ошибка копирования logger.dll: {e}")
                self.log_exception(f"Ошибка копирования logger.dll")
                success = False
        else:
            self.print_error("logger.dll не найден в сборке CMake")
            self.logger.error(f"logger.dll не найден в {build_dir}")
            success = False

        # Ищем и копируем calculate.dll
        calculate_dll_files = list(build_dir.rglob("calculate.dll"))
        if calculate_dll_files:
            source_dll = calculate_dll_files[0]
            target_dll = self.project_root / "src" / "cpp_calculate" / "lib" / "calculate.dll"
            try:
                shutil.copy2(source_dll, target_dll)
                file_size = target_dll.stat().st_size
                self.print_success(f"calculate.dll скопирован ({file_size} байт)")
                self.log_debug(f"calculate.dll скопирован из {source_dll}")
            except Exception as e:
                self.print_error(f"Ошибка копирования calculate.dll: {e}")
                self.log_exception(f"Ошибка копирования calculate.dll")
                success = False
        else:
            self.print_error("calculate.dll не найден в сборке CMake")
            self.logger.error(f"calculate.dll не найден в {build_dir}")
            success = False

        return success

    def test_calculator(self):
        """Тестирование калькулятора"""
        self.print_header("ТЕСТИРОВАНИЕ КАЛЬКУЛЯТОРА")
        self.log_debug("Начало тестирования калькулятора")

        try:
            # Добавляем src в путь Python
            src_path = str(self.project_root / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from cpp_calculate.calculate import CppCalculator

            # Тест 1: Создание калькулятора
            calculator = CppCalculator()
            self.print_success("Калькулятор создан успешно")
            self.log_debug("Калькулятор создан успешно")

            # Тест 2: Простые вычисления
            test_cases = [
                ("1", "1"),
                ("1 + 1", "2"),
                ("2 + 2", "4"),
                ("10 - 5", "5"),
                ("3 * 4", "12"),
                ("8 / 2", "4"),
                ("(2 + 3) * 4", "20"),  # Добавлен тест со скобками
                ("2 + 3 * 4", "14"),    # Приоритет операций
            ]

            for expression, expected in test_cases:
                result = calculator.evaluate(expression)
                if result == expected:
                    self.print_success(f"{expression} = {result}")
                    self.log_debug(f"Тест пройден: {expression} = {result}")
                else:
                    self.print_error(f"{expression} = {result} (ожидалось: {expected})")
                    self.logger.error(f"Тест не пройден: {expression} = {result} (ожидалось: {expected})")
                    return False

            self.print_success("Все тесты калькулятора пройдены!")
            self.log_debug("Все тесты калькулятора пройдены успешно")
            return True

        except Exception as e:
            self.print_error(f"Ошибка тестирования калькулятора: {e}")
            self.log_exception(f"Ошибка тестирования калькулятора")
            return False

    def test_logger(self):
        """Тестирование логгера"""
        self.print_header("ТЕСТИРОВАНИЕ ЛОГГЕРА")
        self.log_debug("Начало тестирования логгера")

        try:
            src_path = str(self.project_root / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from cpp_logger.logger import CppLogger

            logger = CppLogger("test_build.log")
            logger.info("Тест сборки прошел успешно!")
            logger.debug("Отладочное сообщение")
            logger.warning("Предупреждение")
            logger.error("Ошибка (тестовая)")
            
            self.print_success("Логгер работает корректно")
            self.log_debug("Логгер работает корректно")
            return True

        except Exception as e:
            self.print_error(f"Ошибка тестирования логгера: {e}")
            self.log_exception(f"Ошибка тестирования логгера")
            return False

    def build_project(self):
        """Основной метод сборки проекта"""
        self.print_header("🚀 ЗАПУСК УМНОЙ СБОРКИ ПРОЕКТА")
        self.logger.info("НАЧАЛО ПРОЦЕССА СБОРКИ")

        print(f"📁 Рабочая директория: {self.project_root}")
        print(f"📍 Абсолютный путь: {self.project_root.resolve()}")
        self.logger.info(f"Рабочая директория: {self.project_root}")
        self.logger.info(f"Абсолютный путь: {self.project_root.resolve()}")

        # Создаем директории
        self.ensure_directories()

        # Проверяем структуру проекта
        if not self.check_project_structure():
            self.print_error("Критические проблемы со структурой проекта!")
            self.logger.error("Критические проблемы со структурой проекта!")
            return False

        # Проверяем существующие DLL
        if self.check_dlls_exist():
            self.print_success("DLL файлы уже существуют, пропускаем сборку")
            self.logger.info("DLL файлы уже существуют, пропускаем сборку")
            return self.run_tests()

        # Проверяем компиляторы
        compiler_status = self.check_compilers()

        # Пробуем разные способы сборки в порядке приоритета
        build_success = False

        if compiler_status.get('MinGW', False):
            self.print_info("Попытка сборки через MinGW")
            self.logger.info("Попытка сборки через MinGW")
            build_success = self.build_with_mingw()

        if not build_success and compiler_status.get('CMake', False):
            self.print_info("Попытка сборки через CMake...")
            self.logger.info("Попытка сборки через CMake")
            build_success = self.build_with_cmake()

        if not build_success:
            self.print_header("СБОРКА НЕ УДАЛАСЬ")
            self.logger.error("СБОРКА НЕ УДАЛАСЯ - все способы сборки провалились")
            self.print_error("Все способы сборки не увенчались успехом!")
            self.print_info("\n💡 РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ:")
            self.print_info("1. Убедитесь, что Mingw-w64 установлен и доступен в PATH")
            self.print_info("2. Проверьте права доступа к файлам")
            self.print_info("3. Запустите скрипт от имени администратора")
            self.print_info("4. Проверьте, что все исходные файлы присутствуют")
            self.print_info("5. Если используете conda, попробуйте деактивировать окружение")
            return False

        # Финальная проверка DLL
        self.print_header("ФИНАЛЬНАЯ ПРОВЕРКА DLL")
        self.logger.info("Финальная проверка DLL файлов")
        if not self.check_dlls_exist():
            self.print_error("КРИТИЧЕСКАЯ ОШИБКА: DLL файлы не созданы!")
            self.logger.error("КРИТИЧЕСКАЯ ОШИБКА: DLL файлы не созданы!")
            return False

        self.print_success("Сборка завершена успешно!")
        self.logger.info("Сборка завершена успешно!")
        return self.run_tests()

    def run_tests(self):
        """Запускает тесты"""
        self.print_header("ЗАПУСК ТЕСТОВ")
        self.logger.info("Запуск тестов")

        logger_test = self.test_logger()
        calculator_test = self.test_calculator()

        if logger_test and calculator_test:
            self.print_header("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            self.logger.info("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            self.print_success("✅ Структура проекта проверена")
            self.print_success("✅ DLL файлы созданы и проверены")
            self.print_success("✅ Логгер работает корректно")
            self.print_success("✅ Калькулятор вычисляет выражения")
            self.print_success("✅ Проект готов к использованию!")
            return True
        else:
            self.print_error("Некоторые тесты не пройдены!")
            self.logger.error("Некоторые тесты не пройдены!")
            return False


def main():
    """Точка входа"""
    try:
        builder = ProjectBuilder()
        success = builder.build_project()

        if success:
            builder.logger.info("ПРОЦЕСС СБОРКИ ЗАВЕРШЕН УСПЕШНО")
        else:
            builder.logger.error("ПРОЦЕСС СБОРКИ ЗАВЕРШЕН С ОШИБКАМИ")

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Сборка прервана пользователем")
        # Логируем прерывание, если логгер был создан
        if 'builder' in locals():
            builder.logger.warning("Сборка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        # Логируем исключение, если логгер был создан
        if 'builder' in locals():
            builder.logger.exception("Критическая ошибка в основном процессе")
        sys.exit(1)


if __name__ == "__main__":
    main()