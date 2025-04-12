import os
import json
import hashlib
from pathlib import Path
# Remove store_file_entry from import
from app.core.scanner import walk_directory, hash_file, find_duplicates
from app.models.file_entry import FileEntry, Base # Import Base
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine # Import create_engine
from sqlalchemy.pool import StaticPool # Import StaticPool for in-memory DB
import pytest
from typing import Generator

# --- Fixtures for Scanner tests ---

@pytest.fixture(scope="function", name="engine")
def scanner_engine_fixture():
    """Create an in-memory SQLite engine for each scanner test function."""
    # Reason: In-memory DB is fast and isolated for these tests.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # Reason: Ensure tables are created in the in-memory DB.
    Base.metadata.create_all(engine)
    yield engine

@pytest.fixture(scope="function", name="session")
def scanner_session_fixture(engine):
    """Create a new session for each scanner test, rolling back changes."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# --- Tests ---

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

    # Collect the yielded paths (pass Path object)
    found_paths = list(walk_directory(tmp_path))

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
    (tmp_path / "__init__.py").touch() # Should not be skipped by default
    (tmp_path / "file1.txt").touch()
    (tmp_path / ".hidden_dir" / "file2.txt").touch()
    (tmp_path / "__pycache__" / "file3.txt").touch()

    # Collect the yielded paths (pass Path object)
    found_paths = list(walk_directory(tmp_path))

    # Assert that only the non-hidden file and __init__.py were found
    # Note: __init__.py is not typically hidden by the default logic
    assert len(found_paths) == 2
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "__init__.py" in found_paths


def test_walk_directory_skip_symlinks(tmp_path: Path):
    """
    Test that walk_directory skips symbolic links.
    """
    # Create a directory structure with a symlink
    (tmp_path / "file1.txt").touch()
    # Create symlink only if not on Windows or with admin rights
    try:
        os.symlink(tmp_path / "file1.txt", tmp_path / "symlink.txt")
        symlink_created = True
    except OSError:
        symlink_created = False
        pytest.skip("Symlink creation failed (permissions or OS limitation)")


    # Collect the yielded paths (pass Path object)
    found_paths = list(walk_directory(tmp_path))

    # Assert that only the file was found, not the symlink
    assert len(found_paths) == 1
    assert tmp_path / "file1.txt" in found_paths


def test_walk_directory_skip_config(tmp_path: Path):
    """
    Test that walk_directory skips directories listed in the config file.
    """
    # Create a config file
    config_data = {"excluded_directories": ["excluded_dir", "another_excluded"]}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    # Create a directory structure with an excluded directory
    (tmp_path / "excluded_dir").mkdir()
    (tmp_path / "another_excluded").mkdir()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file1.txt").touch()
    (tmp_path / "excluded_dir" / "file2.txt").touch()
    (tmp_path / "another_excluded" / "file3.txt").touch()
    (tmp_path / "subdir" / "file4.txt").touch()


    # Collect the yielded paths (pass Path object and config file path)
    found_paths = list(walk_directory(tmp_path, str(config_file)))

    # Assert that only the non-excluded files were found
    assert len(found_paths) == 2
    assert tmp_path / "file1.txt" in found_paths
    assert tmp_path / "subdir" / "file4.txt" in found_paths
    assert tmp_path / "excluded_dir" / "file2.txt" not in found_paths
    assert tmp_path / "another_excluded" / "file3.txt" not in found_paths


def test_hash_file(tmp_path: Path):
    """
    Test that hash_file returns the correct SHA-256 hash of a file.
    """
    # Create a file with some content
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file."
    file_path.write_bytes(file_content)

    # Calculate the expected hash
    expected_hash = hashlib.sha256(file_content).hexdigest()

    # Calculate the actual hash
    actual_hash = hash_file(file_path)

    # Assert that the hashes match
    assert actual_hash == expected_hash


# Renamed test to reflect its purpose
def test_add_file_entry_to_session(session: Session, tmp_path: Path):
    """
    Test that adding a FileEntry via the session works correctly.
    (Replaces test_store_file_entry)
    """
    # Create a file with some content
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file."
    file_path.write_bytes(file_content)

    # Create a file entry
    file_hash = hash_file(file_path)
    file_stat = file_path.stat()
    file_entry = FileEntry(
        path=str(file_path),
        hash=file_hash,
        size=file_stat.st_size,
        mtime=file_stat.st_mtime,
    )

    # Store the file entry using session.add() and session.flush()
    session.add(file_entry)
    session.flush() # Flush to assign ID

    # Retrieve the file entry from the database using the same session
    retrieved_entry = session.get(FileEntry, file_entry.id)

    # Assert that the file entry was stored correctly
    assert retrieved_entry is not None
    assert retrieved_entry.path == str(file_path)
    assert retrieved_entry.hash == file_hash
    assert retrieved_entry.size == file_stat.st_size
    assert float(retrieved_entry.mtime) == float(file_stat.st_mtime)


def test_find_duplicates(session: Session, tmp_path: Path):
    """
    Test that find_duplicates returns the correct groups of duplicate files.
    """
    # Create some files with duplicate content
    file1_path = tmp_path / "file1.txt"
    file2_path = tmp_path / "file2.txt" # Unique
    file3_path = tmp_path / "file3.txt" # Duplicate of file1
    file4_path = tmp_path / "file4.txt" # Duplicate of file1

    content1 = b"This is duplicate content."
    content2 = b"This is unique content."

    file1_path.write_bytes(content1)
    file2_path.write_bytes(content2)
    file3_path.write_bytes(content1)
    file4_path.write_bytes(content1)

    # Create file entries
    hash1 = hash_file(file1_path) # Should be same as hash3, hash4
    hash2 = hash_file(file2_path) # Should be unique
    hash3 = hash_file(file3_path)
    hash4 = hash_file(file4_path)

    assert hash1 == hash3 == hash4
    assert hash1 != hash2

    entries = [
        FileEntry(path=str(file1_path), hash=hash1, size=file1_path.stat().st_size, mtime=file1_path.stat().st_mtime),
        FileEntry(path=str(file2_path), hash=hash2, size=file2_path.stat().st_size, mtime=file2_path.stat().st_mtime),
        FileEntry(path=str(file3_path), hash=hash3, size=file3_path.stat().st_size, mtime=file3_path.stat().st_mtime),
        FileEntry(path=str(file4_path), hash=hash4, size=file4_path.stat().st_size, mtime=file4_path.stat().st_mtime),
    ]

    # Store the file entries using session.add_all() and session.flush()
    session.add_all(entries)
    session.flush()

    # Find the duplicates using the function from scanner.py
    duplicate_groups = find_duplicates(session) # find_duplicates expects Dict[str, List[str]]

    # Assert that the correct duplicate groups were found
    assert isinstance(duplicate_groups, dict)
    assert len(duplicate_groups) == 1 # Only one group of duplicates
    assert hash1 in duplicate_groups # Check the correct hash is the key
    assert hash2 not in duplicate_groups # Ensure unique file hash is not present

    # Check the paths within the duplicate group (order might vary)
    expected_paths = {str(file1_path), str(file3_path), str(file4_path)}
    actual_paths = set(duplicate_groups[hash1])
    assert actual_paths == expected_paths
    assert len(actual_paths) == 3 # Ensure all 3 duplicates are listed

def test_find_duplicates_no_duplicates(session: Session, tmp_path: Path):
    """
    Test that find_duplicates returns an empty dict when no duplicates exist.
    """
    # Create unique files
    file1_path = tmp_path / "unique1.txt"
    file2_path = tmp_path / "unique2.txt"
    file1_path.write_text("Content A")
    file2_path.write_text("Content B")

    entries = [
        FileEntry(path=str(file1_path), hash=hash_file(file1_path), size=file1_path.stat().st_size, mtime=file1_path.stat().st_mtime),
        FileEntry(path=str(file2_path), hash=hash_file(file2_path), size=file2_path.stat().st_size, mtime=file2_path.stat().st_mtime),
    ]
    session.add_all(entries)
    session.flush()

    duplicate_groups = find_duplicates(session)
    assert duplicate_groups == {} # Expect an empty dictionary

def test_find_duplicates_empty_db(session: Session):
    """
    Test that find_duplicates returns an empty dict for an empty database.
    """
    duplicate_groups = find_duplicates(session)
    assert duplicate_groups == {} # Expect an empty dictionary

