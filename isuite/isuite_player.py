#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import pygame
import numpy as np
import threading
import time
import json
import soundfile as sf
from pathlib import Path
from pygame import sndarray

# Cross-platform directory paths
var_CONFIG_DIR = Path("configs")

class AudioPlayer:
    def __init__(self, config_file="player_config.json"):
        self.config_file = var_CONFIG_DIR / config_file
        self.is_playing = False
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.mixer_sample_rate = None                                # Gespeicherte Sample-Rate des Mixers
        self.thread = None
        self.volume = 1.0                                            # Standard-Lautstärke

        # Lade oder erstelle Konfiguration
        self._load_config()

        pygame.init()                                                # Pygame-Initialisierung

        print("🎵 The audio player is initialized.")

    def _load_config(self):
        """Load or create player configuration from player_config.json."""
        var_default_config = {
            "volume": 0.95
        }

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
            print(f"❌ Error loading or creating player config: {e}. Using default values.")

        # Store parameters
        self.volume = var_default_config["volume"]

    def play_audio(self, audio_file: Path, volume: float = None, callback=None):
        """Spielt Audiodaten ab (Numpy Array)"""
        if volume is None:
            volume = self.volume

        # Lade die Audiodatei
        try:
            var_audio_data, var_sample_rate = sf.read(audio_file)
        except Exception as e:
            print(f"❌ Error reading audio file {audio_file}: {e}")
            return False

        var_duration = len(var_audio_data) / var_sample_rate

        with self.lock:
            if self.is_playing or self.stop_event.is_set():
                print("⚠️ Playback already active or will be stopped.")
                return False

        try:
            print(f"▶️ Start Playback for: {audio_file} @ {var_duration:.2f}s @ {var_sample_rate}Hz @ Volume: {volume}")

            # Verbesserte Mixer-Initialisierung für Windows
            current_init = pygame.mixer.get_init()
            if (current_init is None or
                current_init[0] != var_sample_rate or                # frequency
                self.mixer_sample_rate != var_sample_rate):

                pygame.mixer.quit()
                time.sleep(0.1)                                      # Kurze Pause für Cleanup

                # Versuche verschiedene Buffer-Größen für Windows
                for buffer_size in [1024, 512, 2048, 4096]:
                    try:
                        pygame.mixer.init(
                            frequency=var_sample_rate,
                            size=-16,
                            channels=1,
                            buffer=buffer_size,
                            allowedchanges=0                         # Wichtig für Windows Kompatibilität
                        )
                        print(f"💡 Mixer initialized with buffer size: {buffer_size}")
                        self.mixer_sample_rate = var_sample_rate
                        break
                    except pygame.error as e:
                        print(f"⚠️ Buffer size {buffer_size} failed: {e}")
                        continue
                else:
                    print("❌ All buffer sizes failed")
                    return False

            # Sound direkt aus dem Dateipfad laden
            var_sound = pygame.mixer.Sound(str(audio_file))
            volume = max(0.0, min(volume, 2.0))
            var_sound.set_volume(volume)

            with self.lock:
                self.is_playing = True
                self.stop_event.clear()

            # Starte Playback-Thread
            self.thread = threading.Thread(
                target=self._playback_thread,
                args=(var_sound, var_duration, callback),
                daemon=True
            )
            self.thread.start()

        except Exception as e:
            print(f"❌ Error: {e}")
            with self.lock:
                self.is_playing = False
            return False

        return True

    def _playback_thread(self, var_sound, var_duration: float, callback):
        """Thread-Funktion für Playback"""
        try:
            var_sound.play()

            # Warte bis Ende oder Stopp
            var_start_time = time.time()

            # +0.5 Sekunden Puffer
            while (time.time() - var_start_time < var_duration + 0.5 and
                   not self.stop_event.is_set() and
                   pygame.mixer.get_busy()):
                time.sleep(0.01)

            var_completed = not self.stop_event.is_set() and (pygame.mixer.get_busy() == 0)

        except Exception as e:
            print(f"❌ Thread-Error: {e}")
            var_completed = False
        finally:
            with self.lock:
                self.is_playing = False
                self.stop_event.clear()                              # WICHTIG: Stop-Event zurücksetzen!
            if callback:
                callback(var_completed, var_duration)

    def stop(self):
        """Stoppt die Wiedergabe"""
        with self.lock:
            if not self.is_playing:
                return

            print("⏹️ Stop Playback")
            self.stop_event.set()

        pygame.mixer.stop()                                          # Sofortiger Stopp

    def set_volume(self, volume: float):
        """Setzt Lautstärke (0.0 - 2.0)"""
        with self.lock:
            self.volume = max(0.0, min(volume, 2.0))

    def is_playing_status(self):
        """Gibt den aktuellen Wiedergabestatus zurück"""
        with self.lock:
            return self.is_playing

    def wait_for_completion(self):
        """Wartet auf Abschluss der Wiedergabe"""
        while self.is_playing_status():
            time.sleep(0.01)

    def __del__(self):
        """Ressourcen aufräumen"""
        try:
            pygame.mixer.quit()
        except:
            pass

# Example usage for testing
if __name__ == "__main__":
    try:
        var_audio_file = Path("res/readme_audio.wav")
        var_volume = 1.9

        player = AudioPlayer()
        var_success = player.play_audio(var_audio_file, var_volume)

        if var_success:
            player.wait_for_completion()
            print("Playback completed!")
        else:
            print("Failed to start playback")

    except Exception as e:
        print(f"Error: {e}")
