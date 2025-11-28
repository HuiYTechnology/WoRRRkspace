import os
import ctypes
from pathlib import Path


class CppLogger:
    def __init__(self, filename="app.log"):
        self._dll = None
        self._logger_ptr = None
        self._load_dll()
        self._setup_functions()
        self._create_logger(filename)

    def _load_dll(self):
        """Загружает DLL"""
        dll_path = Path(__file__).parent / "lib" / "logger.dll"

        if not dll_path.exists():
            raise FileNotFoundError(f"DLL not found: {dll_path}")

        self._dll = ctypes.CDLL(str(dll_path))

    def _setup_functions(self):
        """Настраивает функции C++"""
        # create_logger
        self._dll.create_logger.argtypes = [ctypes.c_char_p]
        self._dll.create_logger.restype = ctypes.c_void_p

        # logger_log
        self._dll.logger_log.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        self._dll.logger_log.restype = None

        # delete_logger
        self._dll.delete_logger.argtypes = [ctypes.c_void_p]
        self._dll.delete_logger.restype = None

    def _create_logger(self, filename):
        """Создает логгер в C++"""
        self._logger_ptr = self._dll.create_logger(filename.encode('utf-8'))
        if not self._logger_ptr:
            raise RuntimeError("Failed to create C++ logger")

    def log(self, level, message):
        """Логирует сообщение"""
        if self._logger_ptr:
            self._dll.logger_log(
                self._logger_ptr,
                level.encode('utf-8'),
                message.encode('utf-8')
            )

    def debug(self, message):
        self.log("DEBUG", message)

    def info(self, message):
        self.log("INFO", message)

    def warning(self, message):
        self.log("WARNING", message)

    def error(self, message):
        self.log("ERROR", message)

    def critical(self, message):
        self.log("CRITICAL", message)

    def __del__(self):
        """Деструктор - освобождает ресурсы C++"""
        if hasattr(self, '_logger_ptr') and self._logger_ptr:
            self._dll.delete_logger(self._logger_ptr)