# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import json
from pathlib import Path

def update_config_array(
        source_dir: str,
        config_path: str,
        file_extension: str = "*.onnx"
    ) -> list:
    """Scans a directory for files with the specified extension and saves their names to a JSON array.

    Args:
        source_dir (str): Directory to scan for files (e.g., 'tts/models').
        config_path (str): Path to the output JSON file (e.g., 'configs/tts_model_config.json').
        file_extension (str): File extension to filter (default: '*.onnx').

    Returns:
        list: List of found filenames.
    """
    try:
        source_dir = Path(source_dir)
        config_path = Path(config_path)
        # print(f"Checking directory: {source_dir.resolve()}")
        if not source_dir.exists():
            print(f"❌ Directory {source_dir} does not exist")
            raise FileNotFoundError(f"Directory {source_dir} does not exist")
        
        # Alle Dateien mit der angegebenen Endung auflisten
        files = [file.name for file in source_dir.glob(file_extension)]
        # print(f"Found files: {files}")
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # print(f"Writing to config file: {config_path.resolve()}")
        
        # Dateinamen als JSON-Array speichern
        with open(config_path, 'w') as f:
            json.dump(files, f, indent=4)
        
        # print(f"✅ Successfully saved {len(files)} files to {config_path}")
        return files
    
    except Exception as e:
        print(f"❌ Error updating {config_path}: {e}")
        return []

"""
Verwendung:

    from config_utils import update_config_array

    # Beispiel: Alle .txt-Dateien in eine JSON-Datei speichern
    files = update_config_array(
        source_dir="data/documents",           # Lese Alle Dateien aus dem Ordner: 'data/documents'
        config_path="configs/documents.json",  # Erstelle Config-Datei im Ordner: 'configs/documents.json'
        file_extension="*.txt"                 # Mir die 'txt' Datei-Namen ins Config-Datei als Array abspeichern
    )
    print(files)  # ['doc1.txt', 'doc2.txt']

Das erzeugt eine JSON-Datei wie:
    [
        "doc1.txt",
        "doc2.txt"
    ]
"""
