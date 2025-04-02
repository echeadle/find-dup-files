import os
import json
from typing import Generator
from pathlib import Path


def walk_directory(directory: str, config_file: str = "config.json") -> Generator[Path, None, None]:
    """
    Recursively walks through a directory and yields the paths of all files found.

    Args:
        directory: The path to the directory to walk.
        config_file: The path to the configuration file.

    Yields:
        Path: The path to each file found in the directory.
    """
    excluded_directories = []
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            excluded_directories = config.get("excluded_directories", [])
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_file}' not found. Using default settings.")
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON format in '{config_file}'. Using default settings.")

    for root, dirs, files in os.walk(directory):
        # Skip excluded directories (e.g., .venv, __pycache__, snap, anaconda3)
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__')) and d not in excluded_directories]

        # Skip excluded files (e.g., .hidden_file.txt)
        files[:] = [f for f in files if not f.startswith('.')]

        for file in files:
            file_path = Path(root) / file
            # Skip the config file itself
            if file_path == Path(config_file):
                continue
            if not os.path.islink(file_path):  # Skip symlinks
                yield file_path
