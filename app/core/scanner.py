# /home/echeadle/15_DupFiles/find-dup-files/app/core/scanner.py
from pathlib import Path  # <-- Import Path here
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.file_entry import FileEntry
from typing import Generator, Dict, List
import os
import hashlib
import json

# Function to hash files (assuming this exists or needs to be added)
def hash_file(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The hexadecimal SHA-256 hash of the file content.

    Raises:
        OSError: If the file cannot be read.
    """
    hasher = hashlib.sha256()
    buffer_size = 65536  # Read in 64k chunks
    try:
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(buffer_size)
                if not data:
                    break
                hasher.update(data)
    except OSError as e:
        print(f"Error reading file {file_path} for hashing: {e}")
        raise # Re-raise the exception to be caught by the caller
    return hasher.hexdigest()


def scan_directory(directory: Path, db: Session):
    """
    Scans a directory, hashes files, and stores/updates file entries in the database.

    Args:
        directory (Path): The directory to scan.
        db (Session): The database session.
    """
    # Walk through the directory tree.
    for file_path in walk_directory(directory): # walk_directory now expects Path
        # Get file size and modification time.
        try:
            file_stat = file_path.stat() # Get stat result once
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
        except OSError as e:
            print(f"Warning: Could not stat file {file_path}: {e}")
            continue # Skip this file if stat fails

        # Check if file needs hashing based on DB entry
        existing_entry = db.query(FileEntry).filter_by(path=str(file_path)).first()
        if existing_entry and existing_entry.size == file_size and existing_entry.mtime == file_mtime:
            # File hasn't changed, skip hashing
            continue

        # Hash the file.
        try:
            file_hash = hash_file(file_path)
        except OSError as e:
            print(f"Warning: Could not hash file {file_path}: {e}")
            continue # Skip this file if hashing fails

        # Create or update FileEntry.
        if existing_entry:
            existing_entry.hash = file_hash
            existing_entry.size = file_size
            existing_entry.mtime = file_mtime
            entry_to_save = existing_entry
        else:
            entry_to_save = FileEntry(path=str(file_path), hash=file_hash, size=file_size, mtime=file_mtime)

        # Store or update the file entry in the database.
        try:
            db.add(entry_to_save)
            db.flush() # Flush changes within the loop
        except Exception as e:
            print(f"Error adding/flushing entry for {file_path}: {e}")
            db.rollback() # Rollback if adding this specific entry fails

    try:
        db.commit() # Commit all changes at the end of the scan
    except Exception as e:
        print(f"Error committing changes after scan: {e}")
        db.rollback()


def walk_directory(directory: Path, config_file: str = None) -> Generator[Path, None, None]:
    """
    Recursively walks through a directory and yields the paths of all files found.

    Args:
        directory (Path): The path to the directory to walk.
        config_file (str, optional): The path to the config file. Defaults to None.

    Yields:
        Path: The path to each file found in the directory.
    """
    # Reason: Ensure directory exists before proceeding.
    if not directory.is_dir():
        # Use FileNotFoundError for consistency with os.walk behavior if path doesn't exist
        raise FileNotFoundError(f"Directory '{directory}' not found or is not a directory.")

    excluded_directories = []
    # Reason: Load exclusion config only if specified and exists.
    config_path = Path(config_file) if config_file else None
    if config_path and config_path.is_file():
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
                # Reason: Safely get excluded_directories list, default to empty list if key missing.
                excluded_directories = config_data.get("excluded_directories", [])
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load or parse config file {config_path}: {e}")
            # Continue without exclusions if config fails to load

    # Reason: Use os.walk for efficient directory traversal. Convert Path to string for os.walk.
    for root, dirs, files in os.walk(str(directory)):
        root_path = Path(root)
        # Filter out directories to exclude from further traversal
        # Reason: Modify dirs[:] in-place as required by os.walk API.
        # Reason: Exclude common hidden/system directories and configured exclusions.
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__')) and d not in excluded_directories]

        for file in files:
            # Reason: Exclude common hidden files.
            if file.startswith('.'):
                continue

            file_path = root_path / file

            # Reason: Skip symbolic links as per requirements.
            if file_path.is_symlink():
                continue

            # Reason: Avoid processing the configuration file itself if it's within the scanned directory.
            if config_path and file_path == config_path:
                continue

            # Reason: Yield only valid file paths.
            yield file_path


def find_duplicates(db: Session) -> Dict[str, List[str]]:
    """
    Finds and returns a dictionary of duplicate file groups {hash: [paths]}.

    Args:
        db (Session): The database session.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are file hashes
                              and values are lists of paths for duplicate files.
                              Only includes hashes that appear more than once.
    """
    duplicates_dict = {}

    # Step 1: Find hashes that appear more than once
    # Reason: Subquery efficiently identifies hashes associated with more than one file.
    subquery = (
        select(FileEntry.hash)
        .group_by(FileEntry.hash)
        .having(func.count(FileEntry.id) > 1)
        .subquery()
    )

    # Step 2: Select all file entries whose hash is in the subquery result
    # Reason: Retrieve all FileEntry objects that are part of a duplicate group.
    stmt = select(FileEntry).where(FileEntry.hash.in_(select(subquery.c.hash)))

    # Reason: Execute the query and get all results.
    duplicate_entries = db.execute(stmt).scalars().all()

    # Step 3: Group the paths by hash
    # Reason: Construct the required dictionary format {hash: [path1, path2, ...]}.
    for entry in duplicate_entries:
        if entry.hash not in duplicates_dict:
            duplicates_dict[entry.hash] = []
        duplicates_dict[entry.hash].append(entry.path)

    return duplicates_dict
