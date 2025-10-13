# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import threading
from PySide6.QtCore import QObject, Signal
from isuite import TextToSpeech

# TTS Signal-Klasse
class TTSSignals(QObject):
    completed = Signal(bool, float, str)  # success, audio_length, audio_file

# Erweiterte TTS-Klasse mit Signal-Unterstützung
class TextToSpeechWrapper(TextToSpeech):
    def __init__(self):
        super().__init__()
        self.signals = TTSSignals()
        self._thread = None
        self._stop_event = threading.Event()

    def generate_tts(self, model, text, noise_scale=0.667, noise_w=0.8, length_scale=1.0, output_file=None, callback=None):
        """Start TTS generation and use signal instead of callback."""
        self._stop_event.clear()
        super().generate_tts(model, text, noise_scale, noise_w, length_scale, output_file, self._callback_wrapper)
        return True, 0, output_file

    def _callback_wrapper(self, success, audio_length, result_file):
        """Wrapper to emit signal instead of direct callback."""
        self.signals.completed.emit(success, audio_length, str(result_file) if result_file else None)

    def stop_tts(self):
        """Stop TTS using original stop method."""
        self.stop()
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.1)
