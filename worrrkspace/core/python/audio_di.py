"""
DI контейнер для аудио утилиты проекта Rrrr
"""
import sys
from pathlib import Path
from typing import Optional
from .audio_util import AudioConfig, AudioService, AudioUtility


class AudioDIContainer:
    """Контейнер зависимостей для аудио"""

    def __init__(self):
        self._audio_service: Optional[AudioService] = None
        self._audio_config: Optional[AudioConfig] = None

    def get_audio_service(self) -> AudioService:
        """Получение аудио сервиса (синглтон)"""
        if self._audio_service is None:
            config = self.get_audio_config()
            self._audio_service = AudioUtility(config)
        return self._audio_service

    def get_audio_config(self) -> AudioConfig:
        """Получение конфигурации аудио"""
        if self._audio_config is None:
            # Автоматическое определение пути к конфигу
            config_path = self._find_audio_config()
            self._audio_config = AudioConfig(config_path)
        return self._audio_config

    def _find_audio_config(self) -> str:
        """Поиск конфигурационного файла в проекте"""
        possible_paths = [
            # Для разработки
            Path(__file__).parent.parent / "resources" / "config" / "audio_config.json",
            # Для собранного приложения
            Path(sys.executable).parent / "resources" / "config" / "audio_config.json",
            # Резервный путь
            Path("resources/config/audio_config.json")
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        # Если конфиг не найден, создаем базовый
        print("Audio config not found, using default configuration")
        return ""

    def reset(self):
        """Сброс сервисов (для тестирования)"""
        self._audio_service = None
        self._audio_config = None


# Глобальный экземпляр DI контейнера
audio_di = AudioDIContainer()