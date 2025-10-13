#!/bin/bash

# Activate script as executable
#   chmod +x run_macos_example.sh
#
# Starting in Terminal
#   source bin/ai_env/bin/activate
#   ./run_macos_example.sh

cd "$(dirname "$0")"
source bin/ai_env/bin/activate
python bin/gui_example_tts.py
