from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from pathlib import Path # Import Path

# Import the router from api.routes
from app.api import routes as api_routes
from app.core.db import create_db_engine, create_db_and_tables, get_db_session

# Determine the base directory of the 'app' package
APP_DIR = Path(__file__).resolve().parent
# Static directory is relative to the app directory
STATIC_DIR = APP_DIR / "static"
# Templates directory is relative to the app directory
TEMPLATES_DIR = APP_DIR / "templates" # Define templates directory
# DB file can be relative to the project root (one level up from app)
DB_FILE = APP_DIR.parent / "files.db"

# Create engine and tables globally (or manage through lifespan events)
# Ensure the directory for the DB file exists if it's not in the root
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
engine = create_db_engine(str(DB_FILE))
create_db_and_tables(engine)

def get_app(db_session_override = None) -> FastAPI:
    """
    Creates and configures the FastAPI application instance.

    Args:
        db_session_override (Session, optional): A session to override the default
                                                 dependency, used for testing. Defaults to None.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(title="Duplicate File Finder")

    # --- Dependency Override for Testing ---
    if db_session_override:
        # Define the override function within this scope
        def override_get_db():
            try:
                yield db_session_override
            finally:
                # Test fixture should handle session closing/rollback
                pass
        app.dependency_overrides[get_db_session] = override_get_db
    else:
        # Use the actual dependency generator for the real app
        def actual_get_db():
            session_gen = get_db_session(engine) # Use global engine
            try:
                session = next(session_gen)
                yield session
            finally:
                try:
                    next(session_gen) # Ensure generator cleanup runs
                except StopIteration:
                    pass # Normal finish
                except Exception as e:
                    print(f"Error closing session from generator: {e}")

        app.dependency_overrides[get_db_session] = actual_get_db


    # --- Include API Routes ---
    app.include_router(api_routes.router)

    # --- Static Files and Root Endpoint ---
    # Mount static files (CSS, JS)
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    else:
        print(f"Warning: Static directory not found at {STATIC_DIR}")

    @app.get("/", include_in_schema=False)
    async def read_index():
        """Serves the main index.html file."""
        # Calculate path to index.html within the TEMPLATES directory
        index_path = TEMPLATES_DIR / "index.html" # Look in templates dir
        if index_path.is_file():
            return FileResponse(index_path)
        else:
            # Provide a fallback if index.html is missing
            print(f"Warning: index.html not found at {index_path}")
            return {"message": "Welcome! Frontend file not found."}

    # Favicon endpoint (optional) - relative to project root
    favicon_path = APP_DIR.parent / "favicon.ico"
    if favicon_path.is_file():
        @app.get('/favicon.ico', include_in_schema=False)
        async def favicon():
            return FileResponse(favicon_path)

    return app

# Create the main app instance for Uvicorn to run
app = get_app()
