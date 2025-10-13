#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import json
import os
import re
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile
from pathlib import Path
from datetime import datetime
import threading
import time

# Cross-platform directory paths
var_CONFIG_DIR = Path("configs")
var_AUDIO_DIR = Path("audio") / "wav"
var_UNWANTED_CHARS = r'[^\w\s.,!?-]'

class TextToSpeech:
    def __init__(self, config_file="tts_config.json"):
        self.config_file = var_CONFIG_DIR / config_file
        self._load_config()
        var_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        # Variablen wegen Thread
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.is_busy = False
        self.thread = None
        self.current_process = None

        print("💡 TTS is initialized!")

    def _load_config(self):
        """Load or create TTS configuration from tts_config.json."""
        default_config = {
            "noise_scale": 0.667,  # Stärke des Rauschens in der Synthese (0.0-1.0) default: 0.667
            "noise_w": 0.8,  # Steuert die Breite des Rauschens 'wie weit der Ton vom Original abweicht. default: 0.8
            "length_scale": 1.0  # Geschwindigkeit der Sprache (0.0-2.0) default 1.0
        }

        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                default_config.update(config)
            else:
                # Create default config file
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                # print(f"💡 Created default config file: {self.config_file}")
        except Exception as e:
            print(f"❌ Error loading or creating config: {e}. Using default values.")

        self.noise_scale = default_config["noise_scale"]
        self.noise_w = default_config["noise_w"]
        self.length_scale = default_config["length_scale"]

    def generate_tts(
            self,
            var_model_file,
            text,
            noise_scale=None,
            noise_w=None,
            length_scale=None,
            var_output_file=None,
            callback=None
        ):
        """Generate WAV from text using Piper."""
        var_cleaned_string = re.sub(r'\s+', ' ', text).strip()
        var_cleaned_string = re.sub(var_UNWANTED_CHARS, '', var_cleaned_string)

        if not var_cleaned_string:
            print("⚠️ Empty text after cleaning")
            if callback:
                callback(False, 0, None)
            return False, 0, None

        # Use variables or generate default values
        noise_scale = self.noise_scale if noise_scale is None else noise_scale
        noise_w = self.noise_w if noise_w is None else noise_w
        length_scale = self.length_scale if length_scale is None else length_scale

        # Use provided output file or generate default
        if var_output_file:
            audio_file = Path(var_output_file)
        else:
            var_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = var_AUDIO_DIR / f"tts_{var_timestamp}.wav"

        # print(f"Load Model as 'ONNX Format': {var_model_file}")
        # print(f"Model properties Values: Noise scale: {noise_scale} @ Noise w: {noise_w} @ Length Scale: {length_scale}")
        # print(f"Generating audio for: {text[:50]}...")

        # Check if already busy
        with self.lock:

            if self.is_busy:
                print("⚠️ TTS already active")
                if callback:
                    callback(False, 0, None)
                return False, 0, None

            self.is_busy = True
            self.stop_event.clear()

        # Start TTS in separate thread
        self.thread = threading.Thread(
            target=self._generate_tts_thread,
            args=(
                var_model_file,
                var_cleaned_string,
                noise_scale,
                noise_w,
                length_scale,
                audio_file,
                callback
            ),
            daemon=True
        )
        self.thread.start()

        # Return immediately - the thread will handle the actual work
        return True, 0, audio_file

    def _generate_tts_thread(
            self,
            var_model_file,
            text,
            noise_scale,
            noise_w,
            length_scale,
            audio_file,
            callback
        ):
        """Thread function for TTS generation"""
        success = False
        audio_length = 0
        result_file = None

        try:
            if not text.strip() or not var_model_file:
                print("⚠️ Empty text or no model path")
                return

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as var_process:
                var_temp_path = var_process.name

            try:
                # Build piper command
                var_cmd = [
                    'piper',
                    '--model', str(var_model_file),
                    '--output_file', var_temp_path,
                    '--noise_scale', str(noise_scale),
                    '--noise_w', str(noise_w),
                    '--length_scale', str(length_scale)
                ]

                # Check if stop was requested
                if self.stop_event.is_set():
                    print("⏹️ TTS stopped before starting")
                    return

                # Run piper process
                var_process = subprocess.Popen(
                    var_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Store process reference for potential stopping
                with self.lock:
                    self.current_process = var_process

                # Communicate with process
                stdout, stderr = var_process.communicate(input=text)

                # Check if stop was requested during processing
                if self.stop_event.is_set():
                    var_process.terminate()
                    return

                if var_process.returncode != 0:
                    print(f"❌ Piper error: {stderr}")
                    return

                if not os.path.exists(var_temp_path) or os.path.getsize(var_temp_path) == 0:
                    print("❌ Piper did not create output file")
                    return

                # Process audio file
                sample_rate, audio_data = wavfile.read(var_temp_path)
                audio_length = len(audio_data) / sample_rate

                # Convert audio data
                if audio_data.dtype == np.int16:
                    var_audio_float = audio_data.astype(np.float32) / 32768.0
                else:
                    var_audio_float = audio_data.astype(np.float32)

                # Ensure output directory exists
                audio_file.parent.mkdir(parents=True, exist_ok=True)

                # Save final audio file
                wavfile.write(audio_file, sample_rate, (var_audio_float * 32767.0).astype(np.int16))

                success = True
                result_file = audio_file

            except Exception as e:
                print(f"❌ Error in audio processing: {e}")

            finally:
                # Cleanup temporary file
                if os.path.exists(var_temp_path):
                    os.unlink(var_temp_path)
                with self.lock:
                    self.current_process = None

        except Exception as e:
            print(f"❌ Thread-Error: {e}")

        finally:
            # Update status and call callback
            with self.lock:
                self.is_busy = False
                self.stop_event.clear()

            if callback:
                callback(success, audio_length, result_file)

    def stop(self):
        """Stoppt TTS"""
        with self.lock:
            if not self.is_busy:
                return

            print("⏹️ Stopping TTS generation")
            self.stop_event.set()

            # Terminate the piper process if it's running
            if self.current_process:
                self.current_process.terminate()

    def is_busy_status(self):
        """Gibt den aktuellen Status zurück"""
        with self.lock:
            return self.is_busy

    def wait_for_completion(self):
        """Wartet auf Abschluss der TTS generation (nicht für GUI verwenden!)"""
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=30.0)  # Timeout after 30 seconds

# Example usage for testing
if __name__ == "__main__":
    var_model_file = Path("tts/models/en_GB-cori-high.onnx")  # Test Model
    var_string = "Hello, this is a test. Text to Speech test, it converts text into audio output. Enjoy testing"
    noise_scale = 0.667
    noise_w = 0.8
    length_scale = 1.0
    var_output_file = "audio.wav"

    tts = TextToSpeech()
    # Generate audio
    success, duration, file_path = tts.generate_tts(var_model_file, var_string)

    if success:
        # Warte auf Abschluss der TTS generation
        tts.wait_for_completion()
        print(f"✅ Success! TTS generated audio: {file_path}")
    else:
        print("❌ Failed to generate audio")
