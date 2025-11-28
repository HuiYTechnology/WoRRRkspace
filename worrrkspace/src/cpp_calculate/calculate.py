import os
import ctypes
import sys
from pathlib import Path
import subprocess


class CppCalculator:
    def __init__(self, precision=50):
        self._dll = None
        self._calc_ptr = None
        self._precision = precision
        self._load_dll()
        self._setup_functions()
        self._create_calculator()

    def _load_dll(self):
        """Загружает DLL калькулятора с обработкой ошибок"""
        try:
            # Пробуем несколько путей
            possible_paths = [
                Path(__file__).parent / "lib" / "calculate.dll",
                Path(__file__).parent.parent / "cpp_calculate" / "lib" / "calculate.dll",
                Path(__file__).parent.parent.parent / "src" / "cpp_calculate" / "lib" / "calculate.dll",
                Path(__file__).parent.parent.parent / "src" / "cpp_calculate" / "lib" / "calculate.dll"
            ]

            dll_path = None
            for path in possible_paths:
                abs_path = path.resolve()
                print(f"🔍 Проверка пути: {abs_path} -> Существует: {abs_path.exists()}")
                if abs_path.exists():
                    dll_path = abs_path
                    break

            if not dll_path:
                # Выведем все доступные DLL в проекте для диагностики
                project_root = Path(__file__).parent.parent.parent
                available_files = list(project_root.rglob("*.dll"))
                available_files_str = [str(f.relative_to(project_root)) for f in available_files]
                raise FileNotFoundError(
                    f"Calculate DLL not found in expected locations. "
                    f"Available DLLs: {available_files_str}"
                )

            print(f"🔧 Загрузка DLL: {dll_path}")

            # Добавляем путь к DLL в PATH для поиска зависимостей
            dll_dir = str(dll_path.parent)
            if dll_dir not in os.environ['PATH']:
                os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']

            # Пробуем загрузить DLL
            try:
                self._dll = ctypes.CDLL(str(dll_path))
                print("✅ DLL успешно загружена")
            except OSError as e:
                print(f"⚠️ Первая попытка загрузки не удалась: {e}")
                print("🔄 Попытка загрузки с учетом зависимостей...")

                # Сначала загружаем logger.dll если нужно
                logger_dll_paths = [
                    Path(__file__).parent.parent / "cpp_logger" / "lib" / "logger.dll",
                    Path(__file__).parent.parent.parent / "src" / "cpp_logger" / "lib" / "logger.dll"
                ]

                for logger_path in logger_dll_paths:
                    if logger_path.exists():
                        try:
                            ctypes.CDLL(str(logger_path))
                            print(f"✅ Logger DLL загружена как зависимость: {logger_path}")
                            break
                        except Exception as logger_error:
                            print(f"⚠️ Не удалось загрузить logger.dll {logger_path}: {logger_error}")

                # Пробуем снова загрузить calculate.dll
                self._dll = ctypes.CDLL(str(dll_path))
                print("✅ Calculate DLL успешно загружена после обработки зависимостей")

        except Exception as e:
            raise RuntimeError(f"Failed to load DLL: {e}")

    def _setup_functions(self):
        """Настраивает функции C++"""
        try:
            # create_calculator_with_precision
            self._dll.create_calculator_with_precision.argtypes = [ctypes.c_int]
            self._dll.create_calculator_with_precision.restype = ctypes.c_void_p

            # create_calculator
            self._dll.create_calculator.argtypes = []
            self._dll.create_calculator.restype = ctypes.c_void_p

            # calculate_expression
            self._dll.calculate_expression.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            self._dll.calculate_expression.restype = ctypes.c_void_p

            # delete_calculator
            self._dll.delete_calculator.argtypes = [ctypes.c_void_p]
            self._dll.delete_calculator.restype = None

            # free_result
            self._dll.free_result.argtypes = [ctypes.c_void_p]
            self._dll.free_result.restype = None

            # set_calculator_precision
            self._dll.set_calculator_precision.argtypes = [ctypes.c_void_p, ctypes.c_int]
            self._dll.set_calculator_precision.restype = None

            # get_calculator_precision
            self._dll.get_calculator_precision.argtypes = [ctypes.c_void_p]
            self._dll.get_calculator_precision.restype = ctypes.c_int

        except Exception as e:
            raise RuntimeError(f"Failed to setup function prototypes: {e}")

    def _create_calculator(self):
        """Создает калькулятор в C++"""
        if hasattr(self._dll, 'create_calculator_with_precision'):
            self._calc_ptr = self._dll.create_calculator_with_precision(self._precision)
        else:
            self._calc_ptr = self._dll.create_calculator()

        if not self._calc_ptr:
            raise RuntimeError("Failed to create C++ calculator")
        print("✅ Калькулятор создан успешно")

    def evaluate(self, expression):
        """Вычисляет математическое выражение"""
        if not self._calc_ptr:
            raise RuntimeError("Calculator not initialized")

        try:
            print(f"🔧 Вычисление выражения: {expression}")

            # Кодируем строку в bytes
            expr_bytes = expression.encode('utf-8')

            # Вызываем C++ функцию
            result_ptr = self._dll.calculate_expression(self._calc_ptr, expr_bytes)

            if not result_ptr:
                raise RuntimeError("Calculation returned null")

            # Преобразуем результат в строку
            try:
                result_str = ctypes.string_at(result_ptr).decode('utf-8')
            except Exception as e:
                raise RuntimeError(f"Failed to decode result: {e}")

            # Освобождаем память, выделенную в C++
            if hasattr(self._dll, 'free_result'):
                self._dll.free_result(result_ptr)

            print(f"✅ Результат: {result_str}")
            return result_str

        except Exception as e:
            raise RuntimeError(f"Calculation error: {e}")

    def set_precision(self, precision):
        """Устанавливает точность вычислений"""
        if self._calc_ptr and hasattr(self._dll, 'set_calculator_precision'):
            self._dll.set_calculator_precision(self._calc_ptr, precision)
            self._precision = precision

    def get_precision(self):
        """Возвращает текущую точность вычислений"""
        if self._calc_ptr and hasattr(self._dll, 'get_calculator_precision'):
            return self._dll.get_calculator_precision(self._calc_ptr)
        return self._precision

    def __del__(self):
        """Деструктор - освобождает ресурсы C++"""
        if hasattr(self, '_calc_ptr') and self._calc_ptr and hasattr(self, '_dll'):
            try:
                self._dll.delete_calculator(self._calc_ptr)
                self._calc_ptr = None
            except Exception as e:
                print(f"⚠️ Ошибка при удалении калькулятора: {e}")