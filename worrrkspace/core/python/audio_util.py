import os
import json
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtCore import QUrl, QTimer, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect


class AudioConfig:
    """Конфигурация аудио с учетом структуры проекта Rrrr"""

    def __init__(self, config_path: Optional[str] = None):
        self.music_volume = 0.6
        self.effects_volume = 0.8
        self.fade_duration = 500

        self.music_files: Dict[str, str] = {}
        self.effect_files: Dict[str, str] = {}

        # Базовый путь проекта Rrrr
        self.project_root = Path(__file__).parent.parent

        if config_path:
            self.load_from_json(config_path)

    def load_from_json(self, config_path: str):
        """Загрузка конфигурации для проекта Rrrr"""
        try:
            config_file = Path(config_path)

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Основные настройки
            if 'volume' in config_data:
                self.music_volume = config_data['volume'].get('music', self.music_volume)
                self.effects_volume = config_data['volume'].get('effects', self.effects_volume)

            if 'fade_duration' in config_data:
                self.fade_duration = config_data['fade_duration']

            # Загрузка файлов с разрешением путей относительно проекта Rrrr
            if 'music' in config_data:
                for name, path in config_data['music'].items():
                    self.music_files[name] = str(self._resolve_project_path(path))

            if 'effects' in config_data:
                for name, path in config_data['effects'].items():
                    self.effect_files[name] = str(self._resolve_project_path(path))

        except Exception as e:
            print(f"Error loading audio config: {e}")

    def _resolve_project_path(self, path: str) -> Path:
        """Разрешение путей относительно корня проекта Rrrr"""
        path_obj = Path(path)

        if path_obj.is_absolute():
            return path_obj

        # Пробуем относительно корня проекта
        resolved = self.project_root / path
        if resolved.exists():
            return resolved

        # Возвращаем путь как есть (будет ошибка при загрузке)
        return Path(path)


class AudioService(QObject):
    """Интерфейс аудио сервиса"""

    def play_music(self, name: str, fade_in: bool = True) -> bool:
        raise NotImplementedError

    def play_effect(self, name: str) -> bool:
        raise NotImplementedError

    def stop_music(self, fade_out: bool = True) -> None:
        raise NotImplementedError

    def set_music_volume(self, volume: float) -> None:
        raise NotImplementedError

    def set_effects_volume(self, volume: float) -> None:
        raise NotImplementedError


class AudioUtility(AudioService):
    """Аудио утилита для проекта Rrrr"""

    def __init__(self, config: AudioConfig = None):
        super().__init__()

        self.config = config or AudioConfig()

        # Инициализация плееров
        self.music_player = QMediaPlayer()
        self.music_output = QAudioOutput()
        self.music_player.setAudioOutput(self.music_output)
        self.music_output.setVolume(self.config.music_volume)

        # Система предзагрузки
        self.preloaded_effects: Dict[str, QSoundEffect] = {}

        # Управление fade эффектами
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_step)
        self.is_fading = False

        # Предзагрузка эффектов
        self._preload_effects()

    def _preload_effects(self):
        """Предзагрузка звуковых эффектов"""
        for name, file_path in self.config.effect_files.items():
            if not os.path.exists(file_path):
                print(f"Warning: Effect file not found: {file_path}")
                continue

            try:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(file_path))
                effect.setVolume(self.config.effects_volume)
                self.preloaded_effects[name] = effect
            except Exception as e:
                print(f"Error preloading effect {name}: {e}")

    # ===== AudioService Implementation =====

    def play_music(self, name: str, fade_in: bool = True) -> bool:
        """Воспроизведение музыки по имени"""
        if name not in self.config.music_files:
            print(f"Music '{name}' not found in config")
            return False

        file_path = self.config.music_files[name]
        return self._play_music_file(file_path, fade_in)

    def play_effect(self, name: str) -> bool:
        """Воспроизведение звукового эффекта с наложением"""
        if name not in self.preloaded_effects:
            print(f"Effect '{name}' not found")
            return False

        # Создаем новый экземпляр для наложения
        original_effect = self.preloaded_effects[name]
        new_effect = QSoundEffect()
        new_effect.setSource(original_effect.source())
        new_effect.setVolume(original_effect.volume())
        new_effect.play()

        # Автоочистка
        QTimer.singleShot(10000, new_effect.deleteLater)
        return True

    def stop_music(self, fade_out: bool = True) -> None:
        """Остановка музыки с плавным затуханием"""
        if fade_out and self.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            current_vol = self.music_output.volume()
            self._start_fade(current_vol, 0.0, stop_after_fade=True)
        else:
            self.music_player.stop()
            self.is_fading = False

    def set_music_volume(self, volume: float) -> None:
        """Установка громкости музыки"""
        self.config.music_volume = max(0.0, min(1.0, volume))
        if not self.is_fading:
            self.music_output.setVolume(self.config.music_volume)

    def set_effects_volume(self, volume: float) -> None:
        """Установка громкости эффектов"""
        self.config.effects_volume = max(0.0, min(1.0, volume))
        for effect in self.preloaded_effects.values():
            effect.setVolume(self.config.effects_volume)

    # ===== Internal Methods =====

    def _play_music_file(self, file_path: str, fade_in: bool) -> bool:
        """Внутренний метод воспроизведения музыки"""
        if not os.path.exists(file_path):
            return False

        if self.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_music(fade_out=True)
            QTimer.singleShot(self.config.fade_duration + 100,
                              lambda: self._start_music(file_path, fade_in))
        else:
            self._start_music(file_path, fade_in)
        return True

    def _start_music(self, file_path: str, fade_in: bool):
        """Запуск воспроизведения музыки"""
        try:
            self.music_player.setSource(QUrl.fromLocalFile(file_path))

            if fade_in:
                self.music_output.setVolume(0.0)
                self.music_player.play()
                self._start_fade(0.0, self.config.music_volume)
            else:
                self.music_output.setVolume(self.config.music_volume)
                self.music_player.play()

        except Exception as e:
            print(f"Error playing music: {e}")

    def _start_fade(self, start_volume: float, end_volume: float, stop_after_fade: bool = False):
        """Запуск плавного изменения громкости"""
        self.is_fading = True
        self.fade_start_volume = start_volume
        self.fade_target_volume = end_volume
        self.stop_after_fade = stop_after_fade
        self.fade_steps = 20
        self.current_fade_step = 0
        self.fade_step_size = (end_volume - start_volume) / self.fade_steps

        self.fade_timer.start(self.config.fade_duration // self.fade_steps)

    def _fade_step(self):
        """Шаг плавного изменения громкости"""
        self.current_fade_step += 1

        if self.current_fade_step <= self.fade_steps:
            new_volume = self.fade_start_volume + (self.fade_step_size * self.current_fade_step)
            self.music_output.setVolume(max(0.0, min(1.0, new_volume)))
        else:
            self.fade_timer.stop()
            self.is_fading = False
            if self.stop_after_fade:
                self.music_player.stop()