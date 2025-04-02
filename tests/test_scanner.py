import os
import json
import hashlib
from pathlib import Path
from app.core.scanner import walk_directory, hash_file, store_file_entry, find_duplicates
from app.models.file_entry import FileEntry
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlmodel import Session, select, func
import pytest


def test_walk_directory_basic(tmp_path: Path):
    """
    Test that walk_directory finds all files in a simple directory structure.
    """
    # Create a simple directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "file1.txt").touch()
    (tmp_path / "dir1" / "file2.txt").touch()
    (tmp_path / "dir2" / "file3.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that all files were found
    assert len(found_paths) == 3
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "dir1" / "file2.txt" in found_paths
    assert tmp_path / "dir2" / "file3.txt" in found_paths


def test_walk_directory_skip_hidden(tmp_path: Path):
    """
    Test that walk_directory skips hidden directories and files.
    """
    # Create a directory structure with hidden files and directories
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".hidden_file.txt").touch()
    (tmp_path / "__init__.py").touch()
    (tmp_path / "file1.txt").touch()
    (tmp_path / ".hidden_dir" / "file2.txt").touch()
    (tmp_path / "__pycache__" / "file3.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that only the non-hidden file and the __init__.py file was found
    assert len(found_paths) == 2
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "__init__.py" in found_paths


def test_walk_directory_skip_symlinks(tmp_path: Path):
    """
    Test that walk_directory skips symbolic links.
    """
    # Create a directory structure with a symlink
    (tmp_path / "file1.txt").touch()
    os.symlink(tmp_path / "file1.txt", tmp_path / "symlink.txt")

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path)))

    # Assert that only the file was found, not the symlink
    assert len(found_paths) == 1
    assert tmp_path / "file1.txt" in found_paths


def test_walk_directory_skip_config(tmp_path: Path):
    """
    Test that walk_directory skips directories listed in the config file.
    """
    # Create a config file
    config_data = {"excluded_directories": ["excluded_dir"]}
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Create a directory structure with an excluded directory
    (tmp_path / "excluded_dir").mkdir()
    (tmp_path / "file1.txt").touch()
    (tmp_path / "excluded_dir" / "file2.txt").touch()

    # Collect the yielded paths
    found_paths = list(walk_directory(str(tmp_path), str(config_file)))

    # Assert that only the non-excluded file was found
    assert len(found_paths) == 1
    assert tmp_path / "file1.txt" in found_paths


def test_hash_file(tmp_path: Path):
    """
    Test that hash_file returns the correct SHA-256 hash of a file.
    """
    # Create a file with some content
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file."
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Calculate the expected hash
    expected_hash = hashlib.sha256(file_content).hexdigest()

    # Calculate the actual hash
    actual_hash = hash_file(file_path)

    # Assert that the hashes match
    assert actual_hash == expected_hash


def test_store_file_entry_skip_rehash(tmp_path: Path):
    """
    Test that store_file_entry skips re-hashing files with unchanged size+mtime.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    session_generator = get_db_session(engine)
    session = next(session_generator)

    # Create a file with some content
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file."
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Create a file entry
    file_hash = hash_file(file_path)
    file_size = os.path.getsize(file_path)
    file_mtime = os.path.getmtime(file_path)
    file_entry = FileEntry(
        path=str(file_path),
        hash=file_hash,
        size=file_size,
        mtime=file_mtime,
    )

    # Store the file entry
    store_file_entry(file_entry, session)

    # Retrieve the file entry from the database
    statement = select(FileEntry).where(FileEntry.path == str(file_path))
    db_file_entry = session.exec(statement).first()

    # Assert that the file entry was stored correctly
    assert db_file_entry is not None
    assert db_file_entry.path == str(file_path)
    assert db_file_entry.hash == file_hash
    assert db_file_entry.size == file_size
    assert db_file_entry.mtime == file_mtime

    # Modify the file content
    with open(file_path, "wb") as f:
        f.write(b"This is modified content.")

    # Create a new file entry with the same path, but different content
    new_file_hash = hash_file(file_path)
    new_file_size = os.path.getsize(file_path)
    new_file_mtime = os.path.getmtime(file_path)
    new_file_entry = FileEntry(
        path=str(file_path),
        hash=new_file_hash,
        size=new_file_size,
        mtime=new_file_mtime,
    )

    # Store the new file entry
    store_file_entry(new_file_entry, session)

    # Retrieve the file entry from the database again
    statement = select(FileEntry).where(FileEntry.path == str(file_path))
    db_file_entry = session.exec(statement).first()

    # Assert that the file entry was updated
    assert db_file_entry is not None
    assert db_file_entry.path == str(file_path)
    assert db_file_entry.hash == new_file_hash
    assert db_file_entry.size == new_file_size
    assert db_file_entry.mtime == new_file_mtime

    # Create a new file entry with the same path, size, and mtime
    new_file_entry = FileEntry(
        path=str(file_path),
        hash=new_file_hash,
        size=new_file_size,
        mtime=new_file_mtime,
    )

    # Store the new file entry
    store_file_entry(new_file_entry, session)

    # Retrieve the file entry from the database again
    statement = select(FileEntry).where(FileEntry.path == str(file_path))
    db_file_entry = session.exec(statement).first()

    # Assert that the file entry was not updated
    assert db_file_entry is not None
    assert db_file_entry.path == str(file_path)
    assert db_file_entry.hash == new_file_hash
    assert db_file_entry.size == new_file_size
    assert db_file_entry.mtime == new_file_mtime

    session.close()


def test_find_duplicates(tmp_path: Path):
    """
    Test that find_duplicates returns the correct groups of duplicate files.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    session_generator = get_db_session(engine)
    session = next(session_generator)

    # Create some files with duplicate content
    file1_path = tmp_path / "file1.txt"
    file2_path = tmp_path / "file2.txt"
    file3_path = tmp_path / "file3.txt"
    file4_path = tmp_path / "file4.txt"

    file1_content = b"This is the content of file 1."
    file2_content = b"This is the content of file 2."
    file3_content = b"This is the content of file 1."  # Duplicate of file1
    file4_content = b"This is the content of file 1."  # Duplicate of file1

    with open(file1_path, "wb") as f:
        f.write(file1_content)
    with open(file2_path, "wb") as f:
        f.write(file2_content)
    with open(file3_path, "wb") as f:
        f.write(file3_content)
    with open(file4_path, "wb") as f:
        f.write(file4_content)

    # Create file entries
    file1_hash = hash_file(file1_path)
    file2_hash = hash_file(file2_path)
    file3_hash = hash_file(file3_path)
    file4_hash = hash_file(file4_path)

    file1_entry = FileEntry(
        path=str(file1_path),
        hash=file1_hash,
        size=os.path.getsize(file1_path),
        mtime=os.path.getmtime(file1_path),
    )
    file2_entry = FileEntry(
        path=str(file2_path),
        hash=file2_hash,
        size=os.path.getsize(file2_path),
        mtime=os.path.getmtime(file2_path),
    )
    file3_entry = FileEntry(
        path=str(file3_path),
        hash=file3_hash,
        size=os.path.getsize(file3_path),
        mtime=os.path.getmtime(file3_path),
    )
    file4_entry = FileEntry(
        path=str(file4_path),
        hash=file4_hash,
        size=os.path.getsize(file4_path),
        mtime=os.path.getmtime(file4_path),
    )

    # Store the file entries
    store_file_entry(file1_entry, session)
    store_file_entry(file2_entry, session)
    store_file_entry(file3_entry, session)
    store_file_entry(file4_entry, session)

    # Find the duplicates
    duplicate_groups = find_duplicates(session)

    # Assert that the correct duplicate groups were found
    assert len(duplicate_groups) == 1
    assert len(duplicate_groups[0]) == 3
    assert file1_entry in duplicate_groups[0]
    assert file3_entry in duplicate_groups[0]
    assert file4_entry in duplicate_groups[0]

    session.close()
