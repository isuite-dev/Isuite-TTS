#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# See LICENSE for details.

import os
import shutil
import subprocess
import sys

def cleanup():
    files_to_remove = ['build', 'isuite_tts.egg-info']

    for file_path in files_to_remove:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            print(f"Removed: {file_path}")

if __name__ == "__main__":
    cleanup()
