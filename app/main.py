from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import routes
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.responses import HTMLResponse
import os

def get_app(session: Session = None):
    """
    Creates and configures the FastAPI application.

    Args:
        session: An optional database session for testing.

    Returns:
        A configured FastAPI application instance.
    """
    app = FastAPI()

    # Include the API router
    app.include_router(routes.router, prefix="/api")

    # Set up dependency overrides for database session
    if session is None:
        engine = create_db_engine()
        create_db_and_tables(engine)
        app.dependency_overrides[get_db_session] = lambda: next(get_db_session(engine))
    else:
        app.dependency_overrides[get_db_session] = lambda: session

    # Mount the static files directory
    static_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    # Set up templates
    templates_path = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=templates_path)

    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request, db: Session = Depends(get_db_session)):
        """
        Serves the main HTML page.
        """
        return templates.TemplateResponse(request, "index.html", {"data": {}})

    return app

app = get_app()


if __name__ == "__main__":
    import uvicorn
    app = get_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
