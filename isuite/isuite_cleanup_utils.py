#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

import os
from pathlib import Path
from datetime import datetime, timedelta

class Cleanup:
    def __init__(
        self,
        source_dir: str,
        file_extension: str = "wav"
    ) -> None:

        self.source_dir = Path(source_dir)
        self.file_extension = file_extension

    def cleanup_by_age(self, days=7):
        """Delete files older than the specified number of days."""
        try:
            var_cutoff_time = datetime.now() - timedelta(days=days)
            var_deleted_files = 0

            var_files = "*." + self.file_extension
            for file_path in self.source_dir.glob(var_files):
                var_file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if var_file_mtime < var_cutoff_time:
                    file_path.unlink()
                    # print(f"Deleted old file: {file_path}")
                    var_deleted_files += 1

            return var_deleted_files

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return 0

    def cleanup_specific_file(self, file_paths):
        """Delete specific files."""
        try:
            if not isinstance(file_paths, list):
                var_file_paths = [file_paths]
            else:
                var_file_paths = file_paths

            var_deleted_files = 0

            for file_path in var_file_paths:
                file_path = Path(file_path)

                var_file_ext = "." + self.file_extension
                if file_path.exists() and file_path.suffix == var_file_ext:
                    file_path.unlink()
                    # print(f"Deleted file: {file_path}")
                    var_deleted_files += 1

            return var_deleted_files

        except Exception as e:
            print(f"❌ Error deleting files: {e}")
            return 0

    def list_specific_files(self):
        """Return a list of files with the specified extension in the directory."""
        try:
            var_files = "*." + self.file_extension
            return [str(file_path) for file_path in self.source_dir.glob(var_files)]
        except Exception as e:
            print(f"❌ Error listing audio files: {e}")
            return []

# Example usage for testing
if __name__ == "__main__":
    clean = Cleanup("audio/wav/", "wav")

    # Get all WAV files using the existing method
    var_file_list = clean.list_specific_files()

    if not var_file_list:
        print("⚠️ No files found to delete")
    else:
        # Delete specific files
        deleted_count = clean.cleanup_specific_file(var_file_list)
        # deleted_count = clean.cleanup_by_age(0)

        if deleted_count > 0:
            print(f"✅ Successfully deleted {deleted_count} files")
        else:
            print(f"⚠️ No files found to delete")

""""
## Usage Options:

# Initialize the Cleanup
    clean = Cleanup("audio/wav/", "wav")

# Delete all files older than 7 days
    clean.cleanup_by_age(7)

# Delete all specific files by path
    file_list = clean.list_specific_files()
    clean.cleanup_specific_file(file_list)
"""
