from fastapi.testclient import TestClient
from app.main import get_app
from sqlmodel import Session
import pytest
from app.core.db import create_db_engine, create_db_and_tables, get_db_session

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

def test_index_html_exists(client: TestClient):
    """
    Test that the index.html file is served correctly.
    """
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Duplicate File Finder" in response.text
