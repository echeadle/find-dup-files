import os
import json
import hashlib
from typing import Generator
from pathlib import Path
from sqlmodel import Session
from app.models.file_entry import FileEntry


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


def hash_file(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.

    Args:
        file_path: The path to the file.

    Returns:
        str: The SHA-256 hash of the file.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)  # Read in 4KB chunks
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def store_file_entry(file_entry: FileEntry, session: Session):
    """
    Stores or updates a file entry in the database.

    Args:
        file_entry: The file entry to store or update.
        session: The database session.
    """
    if file_entry.id:
        db_file_entry = session.get(FileEntry, file_entry.id)
        if db_file_entry:
            # Update the existing file entry
            db_file_entry.path = file_entry.path
            db_file_entry.hash = file_entry.hash
            db_file_entry.size = file_entry.size
            db_file_entry.mtime = file_entry.mtime
            session.add(db_file_entry)
        else:
            # Create a new file entry
            session.add(file_entry)
    else:
        session.add(file_entry)
    session.commit()


def scan_directory(directory: str, session: Session, config_file: str = "config.json"):
    """
    Scans a directory and stores the file entries in the database.

    Args:
        directory: The path to the directory to scan.
        session: The database session.
        config_file: The path to the configuration file.
    """
    for file_path in walk_directory(directory, config_file):
        file_hash = hash_file(file_path)
        file_entry = FileEntry(
            path=str(file_path),
            hash=file_hash,
            size=os.path.getsize(file_path),
            mtime=os.path.getmtime(file_path),
        )
        store_file_entry(file_entry, session)
