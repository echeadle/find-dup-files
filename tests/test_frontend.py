from fastapi.testclient import TestClient
# Remove 'templates' from this import
from app.main import get_app
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
# Import necessary DB setup functions and models if needed for setup,
# but get_app handles the dependency override now.
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from app.models.file_entry import Base # Import Base for create_tables
import pytest
import os
from pathlib import Path

# Use a simplified in-memory DB setup for frontend tests,
# as they primarily test HTML serving and basic structure.

@pytest.fixture(scope="function", name="engine")
def fe_engine_fixture():
    """Create an in-memory SQLite engine for each frontend test function."""
    # Reason: In-memory DB is fast and isolated for simple tests.
    # Reason: StaticPool is required for in-memory SQLite with multiple connections/sessions.
    engine = create_engine(
        "sqlite:///:memory:", # Use :memory: for in-memory DB
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # Reason: Ensure tables are created in the in-memory DB.
    Base.metadata.create_all(engine)
    yield engine


@pytest.fixture(scope="function", name="session")
def fe_session_fixture(engine):
    """Create a new session for each frontend test, rolling back changes."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Pytest fixture to create a TestClient with DB override for frontend tests.
    """
    # Define the override function
    def override_get_db():
        yield session

    app = get_app() # Get the app instance
    # Apply the dependency override
    app.dependency_overrides[get_db_session] = override_get_db
    client = TestClient(app)
    yield client
    # Clear overrides after test
    app.dependency_overrides.clear()


def test_index_html_exists(client: TestClient):
    """
    Test that the index.html file is served correctly at the root URL.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Reason: Check if the content type indicates HTML.
    assert "text/html" in response.headers["content-type"]
    # Reason: Check for a key element expected in index.html.
    assert "<h1>Duplicate File Viewer</h1>" in response.text


def test_index_html_has_scan_elements(client: TestClient):
    """
    Test that the index.html file contains the scan input and button.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Reason: Check for the input field by its ID.
    assert '<input type="text" id="scanDir"' in response.text
    # Reason: Check for the button by its ID.
    assert '<button id="scanBtn"' in response.text


def test_index_html_has_results_container(client: TestClient):
    """
    Test that the index.html file contains the results container div.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Reason: Check for the main container where results will be displayed.
    assert '<div class="results" id="resultsContainer">' in response.text


def test_index_html_has_status_message_div(client: TestClient):
    """
    Test that the index.html file contains the status message div.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Reason: Check for the div used to display status updates to the user.
    assert '<div id="statusMessage">' in response.text

# Note: Removed tests checking for specific '<form>' and '<table>' tags
# as the current UI uses divs and JS for interaction, not a traditional form/table.
# Adjusted tests check for key element IDs instead.

