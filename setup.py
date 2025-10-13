#!/usr/bin/env python3
# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# See LICENSE for details.

from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="isuite-tts",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        'isuite': ['tts/models/*.onnx', 'tts/models/*.onnx.json', 'res/*.png', 'res/*.wav'],
    },
    include_package_data=True,
    author="Andrzej Mazur",
    author_email="info@isuite.org",
    description="A Python-based Text-to-Speech system with GUI and CLI interfaces",
    long_description=Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/isuite-dev/Isuite-TTS",
    license="Isuite-TTS Non-Commercial License",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12.0,<=3.13.0",
    install_requires=[
        "numpy==1.26.4",
        "onnxruntime==1.23.0",
        "piper-tts==1.3.0",
        "pygame==2.6.1",
        "PySide6==6.8.0",
        "scipy==1.14.1",
        "soundfile==0.12.1",
        # Add "espeak-ng" if available on PyPI
    ],
)
