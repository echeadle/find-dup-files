import os
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.file_entry import FileEntry
import time
from sqlalchemy import select, func
from typing import Generator
import json

def hash_file(file_path: Path) -> str:
    """
    Hashes a file using SHA-256.

    Args:
        file_path (Path): The path to the file to hash.

    Returns:
        str: The SHA-256 hash of the fil
    """
    # Create a SHA-256 hash object.
    hasher = hashlib.sha256()
    # Open the file in binary read mode.
    with open(file_path, "rb") as file:
        # Read the file in chunks to handle large files.
        while True:
            chunk = file.read(4096)
            if not chunk:
                break  # End of file.
            # Update the hash with the current chunk.
            hasher.update(chunk)
    # Return the hexadecimal representation of the hash.
    return hasher.hexdigest()

def store_file_entry(file_entry: FileEntry, session: Session):
    """
    Stores or updates a file entry in the database.

    Args:
        file_entry: The file entry to store or update.
        session: The database session.
    """
    statement = select(FileEntry).where(FileEntry.path == file_entry.path)
    db_file_entry = session.execute(statement).scalar_one_or_none()
    if db_file_entry:
        # Update the existing file entry if necessary
        if db_file_entry.size != file_entry.size or db_file_entry.mtime != file_entry.mtime:
            db_file_entry.hash = file_entry.hash
            db_file_entry.size = file_entry.size
            db_file_entry.mtime = file_entry.mtime
            session.add(db_file_entry)
    else:
        # Add a new file entry
        session.add(file_entry)
    session.commit()

def walk_directory(directory: str, config_file: str = None) -> Generator[Path, None, None]:
    """
    Recursively walks through a directory and yields the paths of all files found.

    Args:
        directory: The path to the directory to walk.
        config_file: The path to the config file.

    Yields:
        Path: The path to each file found in the directory.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' not found.")

    excluded_directories = []
    if config_file:
        with open(config_file, "r") as f:
            config_data = json.load(f)
            excluded_directories = config_data.get("excluded_directories", [])

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_directories]

        # Skip hidden files
        files = [f for f in files if not f.startswith('.')]

        for file in files:
            file_path = Path(root) / file
            if file_path.is_symlink():
                continue  # Skip symlinks
            if config_file and file_path == Path(config_file):
                continue  # Skip the config file itself
            yield file_path

def scan_directory(directory: Path, db: Session):
    """
    Scans a directory, hashes files, and stores/updates file entries in the database.

    Args:
        directory (Path): The directory to scan.
        db (Session): The database session.
    """
    # Walk through the directory tree.
    for file_path in walk_directory(directory):
        # Get file size and modification time.
        file_size = file_path.stat().st_size
        file_mtime = file_path.stat().st_mtime
        # Hash the file.
        file_hash = hash_file(file_path)

        # Create a new FileEntry.
        file_entry = FileEntry(path=str(file_path), hash=file_hash, size=file_size, mtime=file_mtime)
        # Store or update the file entry in the database.
        store_file_entry(file_entry, db)

def find_duplicates(db: Session):
    """
    Finds and returns a list of duplicate file groups.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of lists of FileEntry objects, where each inner list represents a group of duplicate files.
    """
    # Query the database for FileEntry objects with duplicate hashes.
    duplicate_hashes = db.query(FileEntry.hash).group_by(FileEntry.hash).having(func.count(FileEntry.hash) > 1).all()
    duplicate_hashes = [hash[0] for hash in duplicate_hashes]
    duplicate_groups = []
    for hash in duplicate_hashes:
        duplicate_groups.append(db.query(FileEntry).filter_by(hash=hash).all())
    return duplicate_groups
