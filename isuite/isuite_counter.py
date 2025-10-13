# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import time
from PySide6.QtCore import QTimer

class CountDown:
    def __init__(self, label, timer_duration, timer_update):
        self.label = label
        self.timer_duration = timer_duration
        self.timer_update =  timer_update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.start_time = 0
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            self.timer.start(self.timer_update)  # Update alle xxx.ms
            self.update_countdown()

    def stop(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.label.setText("")

    def update_countdown(self):
        if not self.is_running:
            return
        elapsed = time.time() - self.start_time
        remaining = max(0, self.timer_duration - elapsed)
        # Minuten für lange Dauer (>60s), sonst Sekunden
        if self.timer_duration > 60:
            self.label.setText(f"{remaining / 60:.2f} min.")
        else:
            self.label.setText(f"{remaining:.2f} s.")
        if remaining <= 0:
            self.stop()

class CountUp:
    def __init__(self, label, timer_update):
        self.label = label
        self.timer_update = timer_update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countup)
        self.start_time = 0
        self.is_running = False
        self.elapsed_time = 0

    def start(self):
        if not self.is_running:
            self.start_time = time.time() - self.elapsed_time
            self.is_running = True
            self.timer.start(self.timer_update)  # Update alle xxx.ms
            self.update_countup()

    def stop(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.label.setText("")

    def reset(self):
        self.stop()
        self.elapsed_time = 0
        self.label.setText("0.00 s.")

    def update_countup(self):
        if not self.is_running:
            return
        elapsed = time.time() - self.start_time
        self.elapsed_time = elapsed
        # Minuten für lange Dauer (>60s), sonst Sekunden
        if elapsed > 60:
            self.label.setText(f"{elapsed / 60:.2f} min.")
        else:
            self.label.setText(f"{elapsed:.2f} s.")

"""
# Beispiel für die Verwendung:
    countup = CountUp(self.countdown_label, 100)  # Update alle 100ms
    countup.start()  # Startet den Countup
    countup.stop()   # Stoppt den Countup
    countup.reset()  # Setzt den Countup zurück
"""
