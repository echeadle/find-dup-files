import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
# Remove store_file_entry from import
from app.core.scanner import hash_file
from app.models.file_entry import FileEntry
import pytest

# --- Fixtures for DB tests ---
# (These are simpler than API tests as we don't need the full app/client)

@pytest.fixture(scope="function", name="engine")
def db_engine_fixture(tmp_path: Path):
    """Create a temporary database engine for each test function."""
    db_file = tmp_path / "test_func.db"
    _engine = create_db_engine(str(db_file))
    create_db_and_tables(_engine)
    yield _engine
    # Cleanup (optional, tmp_path usually handles it)
    # db_file.unlink(missing_ok=True)

@pytest.fixture(scope="function", name="session")
def db_session_fixture(engine):
    """Create a new session for each test, rolling back changes."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# --- Tests ---

def test_create_db_engine(tmp_path: Path):
    """
    Test that create_db_engine creates a database engine.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    assert engine is not None
    # Test connection (optional but good)
    try:
        connection = engine.connect()
        connection.close()
    except Exception as e:
        pytest.fail(f"Engine failed to connect: {e}")


def test_create_db_and_tables(tmp_path: Path):
    """
    Test that create_db_and_tables creates the database file and tables.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    assert db_file.is_file()
    # Optional: Check if table exists using reflection
    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert "files" in inspector.get_table_names()


def test_get_db_session(engine): # Use the function-scoped engine fixture
    """
    Test that get_db_session provides a usable database session.
    """
    session_generator = get_db_session(engine)
    try:
        session = next(session_generator)
        assert isinstance(session, Session)
        # Test if session is active
        assert session.is_active
        # Test a simple query
        session.execute(select(1))
    except Exception as e:
        pytest.fail(f"Failed to get or use session: {e}")
    finally:
        # Ensure generator cleanup runs
        try:
            next(session_generator)
        except StopIteration:
            pass # Expected behavior
        except Exception as e:
            print(f"Error during session generator cleanup: {e}")


def test_store_file_entry(session: Session, tmp_path: Path): # Use the session fixture
    """
    Test that adding a FileEntry via the session works correctly.
    """
    # Create a file with some content
    file_path = tmp_path / "test_file.txt"
    file_content = b"This is a test file."
    file_path.write_bytes(file_content)

    # Create a file entry
    file_hash = hash_file(file_path)
    file_mtime = file_path.stat().st_mtime
    file_size = file_path.stat().st_size
    file_entry = FileEntry(
        path=str(file_path),
        hash=file_hash,
        size=file_size,
        mtime=file_mtime,
    )

    # Store the file entry using session.add()
    session.add(file_entry)
    session.flush() # Use flush to assign ID and make it queryable within the transaction

    # Retrieve the file entry from the database using the same session
    # Use session.get() for primary key lookup if ID is known, or query otherwise
    retrieved_entry = session.get(FileEntry, file_entry.id) # Assumes ID is assigned on flush

    # Assert that the file entry was stored correctly
    assert retrieved_entry is not None
    assert retrieved_entry.id == file_entry.id
    assert retrieved_entry.path == str(file_path)
    assert retrieved_entry.hash == file_hash
    assert retrieved_entry.size == file_size
    # Compare mtime as floats for safety
    assert float(retrieved_entry.mtime) == float(file_mtime)

    # Verify it's actually in the DB within the transaction
    statement = select(FileEntry).where(FileEntry.path == str(file_path))
    db_file_entry_queried = session.execute(statement).scalar_one_or_none()
    assert db_file_entry_queried is not None
    assert db_file_entry_queried.id == retrieved_entry.id

# Optional: Add tests for find_duplicates if you want to test it at the DB level
# def test_find_duplicates_logic(session: Session, tmp_path: Path):
#     from app.core.scanner import find_duplicates # Import it here if testing here
#     # ... setup duplicate files and FileEntry objects ...
#     session.add_all([...])
#     session.flush()
#     duplicates = find_duplicates(session)
#     # ... assertions ...

