"""
C++ Calculator package
"""

from .calculate import CppCalculator

# Создаем глобальный экземпляр калькулятора по умолчанию
try:
    calculator = CppCalculator()
except Exception as e:
    calculator = None
    print(f"Failed to create calculator: {e}")

__all__ = ['CppCalculator', 'calculator']
__version__ = '0.1.0'