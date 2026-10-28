#!/usr/bin/env python3
import os
import subprocess
import sys
import venv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"


def venv_python():
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def main():
    python = venv_python()
    if not python.exists():
        print("Creating local virtual environment...")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    subprocess.check_call([
        str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)
    ])
    subprocess.check_call([str(python), str(PROJECT_DIR / "dicom_visualizer.py")])


if __name__ == "__main__":
    main()
