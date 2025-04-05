import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from app.core.scanner import hash_file, store_file_entry
from app.models.file_entry import FileEntry
import pytest


def test_create_db_engine(tmp_path: Path):
    """
    Test that create_db_engine creates a database engine.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    assert engine is not None


def test_create_db_and_tables(tmp_path: Path):
    """
    Test that create_db_and_tables creates the database and tables.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    assert os.path.exists(db_file)


def test_get_db_session(tmp_path: Path):
    """
    Test that get_db_session creates a database session.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    session_generator = get_db_session(engine)
    session = next(session_generator)
    assert session is not None
    session.close()


def test_store_file_entry(tmp_path: Path):
    """
    Test that store_file_entry stores a file entry in the database.
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
    file_entry = FileEntry(
        path=str(file_path),
        hash=file_hash,
        size=os.path.getsize(file_path),
        mtime=os.path.getmtime(file_path),
    )

    # Store the file entry
    store_file_entry(file_entry, session)

    # Retrieve the file entry from the database
    statement = select(FileEntry).where(FileEntry.path == str(file_path))
    db_file_entry = session.execute(statement).scalar_one_or_none()

    # Assert that the file entry was stored correctly
    assert db_file_entry is not None
    assert db_file_entry.path == str(file_path)
    assert db_file_entry.hash == file_hash
    assert db_file_entry.size == os.path.getsize(file_path)
    assert db_file_entry.mtime == os.path.getmtime(file_path)

    session.close()
