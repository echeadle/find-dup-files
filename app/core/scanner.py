import os
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.file_entry import FileEntry
import time

def hash_file(file_path: Path) -> str:
    """
    Hashes a file using SHA-256.

    Args:
        file_path (Path): The path to the file to hash.

    Returns:
        str: The SHA-256 hash of the file.
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

def scan_directory(directory: Path, db: Session):
    """
    Scans a directory, hashes files, and stores/updates file entries in the database.

    Args:
        directory (Path): The directory to scan.
        db (Session): The database session.
    """
    # Walk through the directory tree.
    for root, _, files in os.walk(directory):
        for file in files:
            # Construct the full file path.
            file_path = Path(root) / file
            # Skip symlinks.
            if file_path.is_symlink():
                continue

            # Get file size and modification time.
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime
            # Hash the file.
            file_hash = hash_file(file_path)

            # Check if the file already exists in the database.
            existing_file = db.query(FileEntry).filter_by(path=str(file_path)).first()

            if existing_file:
                # If the file exists, check if it has been modified.
                if existing_file.size != file_size or existing_file.mtime != file_mtime:
                    # Update the file's hash, size, and mtime.
                    existing_file.hash = file_hash
                    existing_file.size = file_size
                    existing_file.mtime = file_mtime
            else:
                # If the file doesn't exist, create a new FileEntry.
                new_file = FileEntry(path=str(file_path), hash=file_hash, size=file_size, mtime=file_mtime)
                db.add(new_file)

            # Commit changes to the database.
            db.commit()
