from fastapi.testclient import TestClient
from app.main import get_app
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlmodel import Session, select
from app.models.file_entry import FileEntry
import pytest
from pathlib import Path
import os


@pytest.fixture(name="session")
def session_fixture(tmp_path: Path):
    db_file = tmp_path / "test.db"
    engine = create_db_engine(str(db_file))
    create_db_and_tables(engine)
    session_generator = get_db_session(engine)
    session = next(session_generator)
    yield session
    session.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
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

    # Send a POST request to /scan
    response = client.post("/scan", json={"directory": str(scan_dir)}, headers={"Content-Type": "application/json"})

    # Assert that the response is successful
    assert response.status_code == 200
    assert response.json() == {"message": f"Scan of directory '{scan_dir}' completed."}


def test_scan_endpoint_not_found(tmp_path: Path, client: TestClient):
    """
    Test that the /scan endpoint returns a 404 error if the directory is not found.
    """
    # Send a POST request to /scan with a non-existent directory
    response = client.post("/scan", json={"directory": str(tmp_path / "non_existent_dir")}, headers={"Content-Type": "application/json"})

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

    # Send a GET request to /files
    response = client.get("/files")

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
