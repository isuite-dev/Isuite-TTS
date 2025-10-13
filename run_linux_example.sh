#!/bin/bash

# Activate script as executable
#   chmod +x run_linux_example.sh
# Activate Virtual Environment
#   source bin/ai_env/bin/activate
# Start script as UI
#   ./run_linux_example.sh

cd "$(dirname "$0")"
source bin/ai_env/bin/activate
python bin/gui_example_tts.py
