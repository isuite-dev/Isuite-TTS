# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

from pathlib import Path
from PySide6.QtCore import QObject, Signal
from isuite import AudioPlayer

# Playback Signal-Klasse
class PlaybackSignals(QObject):
    completed = Signal(bool, float, str)  # success, length, audio_file

class AudioPlayerWrapper(AudioPlayer):
    def __init__(self):
        super().__init__()
        self.signals = PlaybackSignals()

    def play_audio(self, audio_file: Path, volume: float = None, callback=None):
        """Start playback and use signal instead of callback."""
        super().play_audio(audio_file, volume, self._callback_wrapper)
        return True

    def _callback_wrapper(self, success, length):
        """Emit signal instead of direct callback."""
        self.signals.completed.emit(success, length, str(self._last_audio_file) if hasattr(self, '_last_audio_file') else "")

    def _playback_thread(self, var_sound, var_duration, callback):
        """Override to store audio_file for callback."""
        self._last_audio_file = var_sound.get_file() if hasattr(var_sound, 'get_file') else ""
        super()._playback_thread(var_sound, var_duration, callback)
