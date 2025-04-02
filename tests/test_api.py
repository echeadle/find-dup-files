from fastapi.testclient import TestClient
from app.main import get_app
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlmodel import Session
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
