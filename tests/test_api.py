from fastapi.testclient import TestClient
from app.main import get_app
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.file_entry import FileEntry
import pytest
from pathlib import Path
import os


@pytest.fixture(name="session")
def session_fixture(tmp_path: Path):
    """
    Fixture to create a temporary database session for testing.
    """
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    session_generator = get_db_session(engine)
    session = next(session_generator)
    yield session
    session.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Fixture to create a FastAPI TestClient with a dependency override for the database session.
    """
    app = get_app(session)
    return TestClient(app)


def test_scan_endpoint(tmp_path: Path, client: TestClient):
    """
    Test that the /scan endpoint triggers a scan and returns a success message.
    """
    # Create a directory to scan
    scan_dir = tmp_path / "scan_dir"
    scan_dir.mkdir()
    (scan_dir / "file1.txt").touch()

    # Send a POST request to /api/scan
    response = client.post("/api/scan", json={"directory": str(scan_dir)})

    # Assert that the response is successful
    assert response.status_code == 200
    assert response.json() == {"message": f"Scan initiated for directory: {scan_dir}"}


def test_scan_endpoint_not_found(tmp_path: Path, client: TestClient):
    """
    Test that the /scan endpoint returns a 404 error if the directory is not found.
    """
    # Send a POST request to /api/scan with a non-existent directory
    response = client.post("/api/scan", json={"directory": str(tmp_path / "non_existent_dir")})

    # Assert that the response is a 404 error
    assert response.status_code == 404
    assert response.json() == {"detail": f"Directory '{tmp_path / 'non_existent_dir'}' not found."}


def test_get_files_endpoint(tmp_path: Path, client: TestClient, session: Session):
    """
    Test that the /files endpoint returns a list of all scanned files.
    """
    # Create some files
    file1_path = tmp_path / "file1.txt"
    file2_path = tmp_path / "file2.txt"
    file1_content = b"This is the content of file 1."
    file2_content = b"This is the content of file 2."
    with open(file1_path, "wb") as f:
        f.write(file1_content)
    with open(file2_path, "wb") as f:
        f.write(file2_content)

    # Create file entries
    file1_entry = FileEntry(
        path=str(file1_path),
        hash="hash1",
        size=os.path.getsize(file1_path),
        mtime=os.path.getmtime(file1_path),
    )
    file2_entry = FileEntry(
        path=str(file2_path),
        hash="hash2",
        size=os.path.getsize(file2_path),
        mtime=os.path.getmtime(file2_path),
    )

    # Store the file entries
    session.add(file1_entry)
    session.add(file2_entry)
    session.commit()

    # Send a GET request to /api/files
    response = client.get("/api/files")

    # Assert that the response is successful
    assert response.status_code == 200

    # Assert that the response contains the correct files
    files = response.json()
    assert len(files) == 2
    assert files[0]["path"] == str(file1_path)
    assert files[0]["hash"] == "hash1"
    assert files[0]["size"] == os.path.getsize(file1_path)
    assert files[0]["mtime"] == os.path.getmtime(file1_path)
    assert files[1]["path"] == str(file2_path)
    assert files[1]["hash"] == "hash2"
    assert files[1]["size"] == os.path.getsize(file2_path)
    assert files[1]["mtime"] == os.path.getmtime(file2_path)


def test_get_duplicates_endpoint(tmp_path: Path, client: TestClient, session: Session):
    """
    Test that the /duplicates endpoint returns a list of duplicate file groups.
    """
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
    file1_hash = "hash1"
    file2_hash = "hash2"
    file3_hash = "hash1"
    file4_hash = "hash1"

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
    session.add(file1_entry)
    session.add(file2_entry)
    session.add(file3_entry)
    session.add(file4_entry)
    session.commit()

    # Send a GET request to /api/duplicates
    response = client.get("/api/duplicates")

    # Assert that the response is successful
    assert response.status_code == 200

    # Assert that the response contains the correct duplicate groups
    duplicate_groups = response.json()
    assert len(duplicate_groups) == 3
    assert duplicate_groups[0]["path"] == str(file1_path)
    assert duplicate_groups[1]["path"] == str(file3_path)
    assert duplicate_groups[2]["path"] == str(file4_path)
