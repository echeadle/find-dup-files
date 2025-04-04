from fastapi.testclient import TestClient
from app.main import get_app
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool
from app.core.db import get_db_session
from app.models.file_entry import FileEntry
import pytest
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# Create a Jinja2Templates instance
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "app", "templates")
)

@pytest.fixture(name="session")
def session_fixture():
    """
    Pytest fixture to create an in-memory SQLite database session for testing.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    session = Session(engine)
    yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Pytest fixture to create a TestClient for testing the FastAPI application.
    """
    app = get_app(session)
    client = TestClient(app)
    yield client

def test_index_html_exists(client: TestClient):
    """
    Test that the index.html file is served correctly.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_index_html_has_form(client: TestClient):
    """
    Test that the index.html file contains the scan form.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "<form" in response.text

def test_index_html_has_duplicates_table(client: TestClient):
    """
    Test that the index.html file contains the duplicates table.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "<table" in response.text

def test_index_html_has_status_and_error_divs(client: TestClient):
    """
    Test that the index.html file contains the status and error divs.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "<div id=\"status\">" in response.text
    assert "<div id=\"error\">" in response.text
