#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import scipy.io.wavfile as wavfile
import numpy as np
from pathlib import Path
from datetime import datetime
from isuite import AudioPlayer, TextToSpeech
import os
import argparse

def main():
    # Default Parameter
    model_file_en = Path("tts") / "models" / "en_GB-cori-high.onnx"
    model_file_fr = Path("tts") / "models" / "fr_FR-siwis-medium.onnx"
    noise_scale = 0.667
    noise_w = 0.8
    length_scale = 1.0
    default_text = "Hello! This is a TTS example. A text conversion to an audio file that will be played back."
    volume = 1.0

    # Argument Parser
    parser = argparse.ArgumentParser(description='Isuite-TTS CLI Example')
    parser.add_argument('--text', type=str, help='Text to convert to speech')
    parser.add_argument('--language', type=str, help='Language Speaker (en or fr)')
    args = parser.parse_args()

    # TTS und AudioPlayer Instanzen
    tts = TextToSpeech()
    player = AudioPlayer()

    output_file = Path("audio") / "wav" / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Verarbeite Parameter
    text = args.text if args.text is not None else default_text

    # Bestimme Modell basierend auf Sprache
    model = model_file_en

    # Überprüfe die Sprache und passe das Modell an
    if args.language == 'fr':
        model = model_file_fr
        print("Using French model")
    elif args.language == 'en':
        model = model_file_en
        print("Using English model")
    else:
        # Fallback auf Englisch bei ungültiger Sprache oder wenn keine Sprache angegeben ist
        if args.language is not None:
            print(f"⚠️ Countries Local '{args.language}' not supported, therefore fallback to EN.")
        else:
            print("No language specified, using English by default")

    try:
        # Generiere TTS mit den definierten Parametern und Modell
        success, audio_length, audio_file = tts.generate_tts(
            model,
            text,
            noise_scale,
            noise_w,
            length_scale
        )

        print("⌛ Please wait... TTS is being generated...")

        # Warte auf Abschluss der TTS-Generierung
        tts.wait_for_completion()
        print("✅ Success! TTS was generated")

        if not success or not audio_file:
            print("❌ Failed to generate audio")
            return

        # Spiele Audio ab
        player.play_audio(
            audio_file=audio_file #, volume=volume
        )
        # Warte auf Abspielung
        player.wait_for_completion()
        print("✅ Success! Audio file was generated and played 😄")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

"""
Verwendung:

(1.) mit Help info:
    python bin/cli_example_tts.py --help

usage: cli_example_tts.py [-h] [--text TEXT] [--language {en,fr}]

Isuite-TTS CLI Example

options:
  -h, --help          show this help message and exit
  --text TEXT         Text to convert to speech
  --language {en,fr}  Language Speaker (en or fr)

(2.) Ohne Parameter (Text: default, Language: En):
    python bin/cli_example_tts.py

(3.) Mit Text und Sprache:
    python bin/cli_example_tts.py --text "This is a TTS example." --language en

(4.) Französischer Sprace:
python bin/cli_example_tts.py --text "Ceci est un exemple de TTS." --language fr

(5.) Mit ungültiger Sprache (Fallback auf Englisch):
python bin/cli_example_tts.py --text "Test if Not Suported Speaker, Fallback Englisch" --language es
"""
