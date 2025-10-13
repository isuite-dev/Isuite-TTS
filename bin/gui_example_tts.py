#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import os
import sys
import json
import time
import random
import numpy as np
import scipy.io.wavfile as wavfile
import threading

from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QComboBox, QPushButton, QLabel, QCheckBox, QMessageBox,
    QSlider, QGroupBox, QStatusBar, QSpacerItem, QSizePolicy, QProgressBar)
from PySide6.QtCore import Qt, QTimer, QObject, Signal, Slot
from PySide6.QtGui import QScreen, QIcon
from isuite import GuiStyles, TextToSpeech, CountDown, CountUp, AudioPlayer, Cleanup, update_config_array
from gui_tts import TextToSpeechWrapper
from gui_player import AudioPlayerWrapper

TIME_PER_CHAR = 0.02  # Mittelwert durch Tests ermittelt

description = """
<br><b>💡 App Description (Brief)</b><br>This example demonstrates text‑to‑speech conversion using a cross‑platform library.<br>It can be used in private, non‑commercial Python projects.
"""

class TTSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = Path("configs") / "gui_config.json"
        self._load_config()
        self.setWindowIcon(QIcon(str(Path(__file__).parent.parent / "res" / "icon.png")))
        self.setWindowTitle("Isuite-TTS GUI Example")
        self.setGeometry(100, 100, self.gui_width, self.gui_height)
        self.center_window()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.counter_down = None
        self.counter_up = None

        # Initialize 'Isuite-tts' Library
        self.tts = TextToSpeechWrapper()
        self.tts.signals.completed.connect(self.tts_callback)

        # Initialize 'Isuite-AudioPlayer' Library
        self.player = AudioPlayerWrapper()
        self.player.signals.completed.connect(self.playback_callback)
        self.is_playing = False

        # Optional Lösche Audio File
        self.cleanup = Cleanup("audio/wav/")

        # 1. ONNX Modelle aus Verzeichnis lesen und ins Config schreiben
        self.source_dir = Path("tts") / "models"
        self.tts_models = update_config_array(source_dir=self.source_dir, config_path="configs/tts_models_config.json", file_extension="*.onnx")

        # 2. PIPER-TTS Eigenschaften ais Config holen
        tts_config_path = Path("configs") / "tts_config.json"
        try:
            with open(tts_config_path, 'r') as f:
                tts_config = json.load(f)
            self.noise_scale = float(tts_config.get("noise_scale", 0.667))
            self.noise_w = float(tts_config.get("noise_w", 0.8))
            self.length_scale = float(tts_config.get("length_scale", 1.0))
            print(f"Assigned for TTS: noise_scale={self.noise_scale}, noise_w={self.noise_w}, length_scale={self.length_scale}")
        except Exception as e:
            print(f"❌ Error loading tts_config.json: {e}")
            self.noise_scale = 0.667
            self.noise_w = 0.8
            self.length_scale = 1.0

        # 3. Pygame-AudioPlayer Eigenschaften aus Config holen
        player_config_path = Path("configs") / "player_config.json"
        try:
            with open(player_config_path, 'r') as f:
                player_config = json.load(f)
            self.volume = player_config.get("volume", 1.0)
        except Exception as e:
            print(f"❌ Error loading player_config.json: {e}")
            self.volume = 1.0

        self.playback_progress = QProgressBar()
        self.playback_progress.setTextVisible(False)
        self.playback_progress.setFixedHeight(8)
        self.playback_progress.setRange(0, 100)
        self.playback_progress.setValue(0)
        self.playback_progress.setStyleSheet(GuiStyles.create_progressbar_styles())
        # Animation Timer für Playback ProgressBar
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.playback_animation)
        self.random_values = []

        # Create GUI layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("QLabel { font-size: 14px; color: #00838F; }")
        layout.addWidget(description_label)

        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(300)
        self.text_input.setPlaceholderText("Enter text to convert to speech...")
        self.text_input.setStyleSheet(GuiStyles.create_textedit_styles())
        layout.addSpacerItem(QSpacerItem(0, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addStretch()
        layout.addWidget(self.text_input)

        language_layout = QHBoxLayout()
        language_layout.addSpacerItem(QSpacerItem(15, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        language_label = QLabel("Select Voice:")
        language_layout.addWidget(language_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.tts_models)  # Beispiel: Modelle in eine ComboBox laden
        self.model_combo.setFixedWidth(200)
        language_layout.addWidget(self.model_combo)
        language_layout.addStretch()
        layout.addLayout(language_layout)

        cleanup_layout = QHBoxLayout()
        cleanup_layout.addSpacerItem(QSpacerItem(15, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.cleanup_checkbox = QCheckBox("Delete all audio files on exit")
        cleanup_layout.addWidget(self.cleanup_checkbox)
        cleanup_layout.addSpacerItem(QSpacerItem(15, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        cleanup_layout.addStretch()
        layout.addLayout(cleanup_layout)

        # === TTS-Controls Group ===
        tts_controls_group = QGroupBox("TTS-Controls")
        tts_controls_layout = QVBoxLayout()
        tts_controls_layout.setSpacing(5)
        tts_controls_layout.setContentsMargins(15, 5, 15, 15)
        tts_controls_group.setStyleSheet(GuiStyles.create_groupbox_styles("#888888", "#FFFFFF"))

        # TTS Noise scale Regler
        self.noise_scale_label = QLabel(f"Noise-Scale: {self.noise_scale:.3f}")
        tts_controls_layout.addWidget(self.noise_scale_label)
        self.noise_scale_slider = QSlider(Qt.Horizontal)
        self.noise_scale_slider.setRange(0, 100)
        self.noise_scale_slider.setValue(int(self.noise_scale * 100))
        self.noise_scale_slider.valueChanged.connect(self.update_noise_scale)
        tts_controls_layout.addWidget(self.noise_scale_slider)

        # TTS Noise w Regler
        self.noise_w_label = QLabel(f"Noise-W: {self.noise_w:.2f}")
        tts_controls_layout.addWidget(self.noise_w_label)
        self.noise_w_slider = QSlider(Qt.Horizontal)
        self.noise_w_slider.setRange(0, 100)
        self.noise_w_slider.setValue(int(self.noise_w * 100))
        self.noise_w_slider.valueChanged.connect(self.update_noise_w)
        tts_controls_layout.addWidget(self.noise_w_slider)

        # TTS Length scale Regler
        self.length_scale_label = QLabel(f"Length-Scale: {self.length_scale:.2f}")
        tts_controls_layout.addWidget(self.length_scale_label)
        self.length_scale_slider = QSlider(Qt.Horizontal)
        self.length_scale_slider.setRange(0, 200)
        self.length_scale_slider.setValue(int(self.length_scale * 100))
        self.length_scale_slider.valueChanged.connect(self.update_length_scale)
        tts_controls_layout.addWidget(self.length_scale_slider)

        tts_controls_group.setLayout(tts_controls_layout)
        tts_controls_group.setFixedWidth(400)
        layout.addWidget(tts_controls_group, alignment=Qt.AlignCenter)

        # === Player Group ===
        player_group = QGroupBox("Player")
        player_layout = QVBoxLayout()
        player_layout.setSpacing(10)
        player_layout.setContentsMargins(15, 5, 15, 15)
        player_group.setStyleSheet(GuiStyles.create_groupbox_styles("#888888", "#FFFFFF"))

        # Player Volume Regler
        self.volume_label = QLabel(f"Volume: {self.volume:.2f}")
        player_layout.addWidget(self.volume_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(int(self.volume * 100))
        self.volume_slider.valueChanged.connect(self.update_volume)
        player_layout.addWidget(self.volume_slider)

        # Playback Progress Bar
        player_layout.addWidget(self.playback_progress)
        player_group.setLayout(player_layout)
        player_group.setFixedWidth(400)
        layout.addWidget(player_group, alignment=Qt.AlignCenter)

        # === Buttons Group (outside) ===
        button_group = QGroupBox("Controls")
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(15, 5, 20, 0)
        button_group.setStyleSheet(GuiStyles.create_groupbox_styles("#E1E1E1", "#222222"))

        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("⌛ Generate and Play Audio  ")
        self.start_button.clicked.connect(self.start_clicked)
        buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ STOP")
        self.stop_button.clicked.connect(self.stop_clicked)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)

        exit_button = QPushButton("🔚 EXIT")
        exit_button.clicked.connect(self.close)
        buttons_layout.addWidget(exit_button)
        button_layout.addLayout(buttons_layout)

        counter_layout = QHBoxLayout()
        counter_layout.setAlignment(Qt.AlignLeft)
        self.counter_titel = QLabel()
        counter_layout.addWidget(self.counter_titel)
        self.counter_label = QLabel()
        counter_layout.addWidget(self.counter_label)

        button_layout.addLayout(counter_layout)
        button_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        button_group.setLayout(button_layout)
        button_group.setFixedWidth(400)
        layout.addWidget(button_group, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addStretch()

        self.status_bar.showMessage("✅ GUI Example is raedy...")

    def _load_config(self):
        var_default_config = {"gui_width": 810, "gui_height": 810, "text_length": 900, "time_per_char": TIME_PER_CHAR}
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    var_config = json.load(f)
                var_default_config.update(var_config)
            else:
                # Create default config file
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(var_default_config, f, indent=4)
                print(f"💡 Created default config file: {self.config_file}")
        except Exception as e:
            print(f"❌ Error loading or creating GUI config: {e}. Using default values.")

        # Store parameters
        self.gui_width = var_default_config["gui_width"]
        self.gui_height = var_default_config["gui_height"]
        self.max_length = var_default_config["text_length"]
        self.time_per_char = var_default_config["time_per_char"]

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.setGeometry(x, y, size.width(), size.height())

    def update_noise_scale(self):
        """Update noise_scale based on slider and show in status bar."""
        self.noise_scale = self.noise_scale_slider.value() / 100.0
        self.noise_scale_label.setText(f"Noise-Scale: {self.noise_scale:.3f}")
        self.status_bar.showMessage(f"Noise-Scale set to {self.noise_scale:.3f}")

    def update_noise_w(self):
        """Update noise_w based on slider and show in status bar."""
        self.noise_w = self.noise_w_slider.value() / 100.0
        self.noise_w_label.setText(f"Noise-W: {self.noise_w:.2f}")
        self.status_bar.showMessage(f"Noise-W set to {self.noise_w:.2f}")

    def update_length_scale(self):
        """Update length_scale based on slider and show in status bar."""
        self.length_scale = self.length_scale_slider.value() / 100.0
        self.length_scale_label.setText(f"Length-Scale: {self.length_scale:.2f}")
        self.status_bar.showMessage(f"Length-scale set to {self.length_scale:.2f}")

    def update_volume(self):
        """Update volume based on slider and show in status bar."""
        volume = self.volume_slider.value() / 100.0
        self.volume_label.setText(f"Volume: {volume:.2f}")
        self.status_bar.showMessage(f"🔊 Volume set to {volume:.2f}")
        return volume

    def reset_controls(self):
        self.stop_countDown()
        self.stop_countUp()
        # Setze Buttons Status zurück
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # Setze Regler Status zurück
        self.noise_scale_slider.setEnabled(True)
        self.noise_w_slider.setEnabled(True)
        self.length_scale_slider.setEnabled(True)
        self.volume_slider.setEnabled(True)

    def start_countDown(self, t_duration, t_update):
        if self.counter_down is None:
            self.counter_down = CountDown(label=self.counter_label, timer_duration = t_duration, timer_update = t_update)
            self.counter_down.start()

    def stop_countDown(self):
        if self.counter_down:
            self.counter_down.stop()
            self.counter_down = None
            self.counter_titel.setText("")
            self.counter_label.setText("")

    def start_countUp(self, t_update):
        if self.counter_up is None:
            self.counter_up = CountUp(label=self.counter_label, timer_update = t_update)
            self.counter_up.start()

    def stop_countUp(self):
        if self.counter_up:
            self.counter_up.stop()
            self.counter_up = None
            self.counter_titel.setText("")
            self.counter_label.setText("")

    def start_clicked(self):
        # get Text from TextEdit
        text = self.text_input.toPlainText()

        if len(text) < 5:
            QMessageBox.warning(self, "No text was found", "You must enter a word (min. 5 letters) in the text field so that it can be played back as audio...")
            self.status_bar.showMessage("⚠️ No text was found")
        else:
            if len(text) > self.max_length:
                QMessageBox.warning(self,"Text Too Long", f"Text exceeds {self.max_length} characters. Please use a shorter text for the demo.")
                self.status_bar.showMessage(f"⚠️ The text is '{len(text)-self.max_length}' letters too long!")
            else:
                self.start_generate_tts(text)

    def start_generate_tts(self, text):
        """Generate TTS in a separate thread."""
        # Selected TTS Model aus dem Pfad: 'tts/models' (e.g., 'en_GB-cori-high.onnx')
        model = self.source_dir / self.model_combo.currentText()
        # definiere WAV-Filename für TTS
        output_file = Path("audio") / "wav" / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

        # Check if the model exists and is larger than 10 MB (to detect LFS pointers)
        if not model.exists() or model.stat().st_size < 10 * 1024 * 1024:
            QMessageBox.warning(self, "No TTS Model Installed",
                "No TTS language model is installed or the model is invalid. "
                "A valid TTS model must be present in the `tts/models/` directory for speech synthesis. "
                "For detailed instructions, see the README section: “Integrating Optional Additional Models (ONNX)”. "
                "Alternatively, please download the full ZIP from the release, which includes all TTS models."
                "https://github.com/isuite-dev/Isuite-TTS/releases/"
            )
            self.status_bar.showMessage("⚠️ No TTS model is installed!")
            return

        # UI update
        self.status_bar.showMessage("⚙️ Generating audio. Please wait...")
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.noise_scale_slider.setEnabled(False)
        self.noise_w_slider.setEnabled(False)
        self.length_scale_slider.setEnabled(False)
        self.volume_slider.setEnabled(False)

        # Countdown starten
        self.counter_titel.setText("⚙️ ")
        value = len(text) * self.time_per_char * (self.length_scale / 1.0)
        self.start_countDown(value, 100)

        # TTS-Duration fürs Status
        self.start_time = time.time()
        # Generate audio
        self.tts.generate_tts(model, text, self.noise_scale, self.noise_w, self.length_scale, output_file, )

    @Slot(bool, float, str)
    def tts_callback(self, success, audio_length, audio_file):
        """Handle TTS completion."""
        self.stop_countDown()
        self.end_time = time.time()

        if success:
            self.status_bar.showMessage(f"✅ TTS completed: {audio_file} @ duration: {audio_length:.2f}s")
            # Starte Audio Playback
            self.play_audio(audio_file, audio_length, self.volume_slider.value())
        else:
            self.status_bar.showMessage("⏹ Stopping TTS generation")
            self.reset_controls()

    def play_audio(self, audio_file, audio_length, volume_slider):
        # Generate random values for playback animation
        num_steps = int(audio_length * 1000 / 100)
        self.random_values = [random.uniform(0.2, 0.8) for _ in range(num_steps)]

        try:
            success = self.player.play_audio(Path(audio_file), volume_slider / 100.0)
            if not success:
                self.status_bar.showMessage("❌ Failed to start playback")
                self.is_playing = False
                self.reset_controls()
            else:
                # CountUp starten
                self.counter_titel.setText("▶️ ")
                self.start_countUp(100)
                self.is_playing = True
                self.status_bar.showMessage(f"🎵 Playing audio ({audio_length:.2f}s)...")
                # Starte ProgressBar-Animation
                self.playback_timer.start(100)  # Update alle 100ms
        except Exception as e:
            self.status_bar.showMessage(f"❌ Error reading or playing audio: {e}")
            self.is_playing = False
            self.reset_controls()

    @Slot(bool, float, str)
    def playback_callback(self, success, length, audio_file):
        self.stop_countUp()
        self.is_playing = False
        self.playback_timer.stop()
        self.playback_progress.setValue(0)
        if success:
            self.status_bar.showMessage(f"💡 Playback completed: {length:.2f}s ⚙️ TTS Duration: {self.end_time-self.start_time:.2f}s")
            self.reset_controls()
        else:
            self.status_bar.showMessage("⏹ Stop Playback")
            self.reset_controls()

    def playback_animation(self):
        """Update the playback progress bar with random values."""
        if not self.is_playing:
            self.playback_timer.stop()
            self.playback_progress.setValue(0)
            return

        if self.random_values:
            value = self.random_values.pop(0)
            self.playback_progress.setValue(int(value * 100))
        else:
            self.playback_timer.stop()
            self.playback_progress.setValue(0)

    def stop_clicked(self):
        self.tts.stop_tts()
        self.player.stop()
        self.playback_timer.stop()
        self.playback_progress.setValue(0)
        self.is_playing = False
        self.status_bar.showMessage("🛑 TTS or Playback stopped.")
        self.reset_controls()

    def closeEvent(self, event):
        """Handle app close event: stop playback and cleanup WAV files if requested."""
        self.status_bar.showMessage("💡 Closing app...")
        try:
            # Library Threads Stoppen
            self.tts.stop_tts()
            self.stop_countDown()
            self.stop_countUp()
            self.player.stop()
            self.playback_timer.stop()
            # Wait briefly to ensure the playback thread terminates
            time.sleep(0.1)
            print("💡 The 'isuite-tts' app has been closed....")
        except Exception as e:
            print(f"❌ Error stopping audio on close: {e}")
        if self.cleanup_checkbox.isChecked():
            audio_dir = Path("audio") / "wav"
            deleted_files = 0
            if audio_dir.exists():
                for file_path in audio_dir.glob("*.wav"):
                    try:
                        file_path.unlink()
                        deleted_files += 1
                    except Exception as e:
                        print(f"❌ Error deleting audio file {file_path}: {e}")
                print(f"Cleanup on exit: {deleted_files} WAV files deleted")
            # Ensure audio/wav/ directory exists after cleanup
            audio_dir.mkdir(parents=True, exist_ok=True)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TTSWindow()
    window.show()
    sys.exit(app.exec())
