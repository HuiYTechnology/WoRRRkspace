"""
C++ Logger package
"""

from .logger import CppLogger

# Создаем глобальный экземпляр логгера по умолчанию
try:
    logger = CppLogger("app.log")
except Exception as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FallbackLogger")
    logger.warning(f"Using Python fallback logger: {e}")

__all__ = ['CppLogger', 'logger']
__version__ = '0.1.0'