from fastapi import FastAPI, Depends
from app.api import routes
from app.core.db import create_db_engine, create_db_and_tables, get_db_session
from sqlmodel import Session

def get_app(session: Session = None):
    app = FastAPI()
    app.include_router(routes.router)
    if session is None:
        engine = create_db_engine()
        create_db_and_tables(engine)
        app.dependency_overrides[get_db_session] = lambda: next(get_db_session(engine))
    else:
        app.dependency_overrides[get_db_session] = lambda: session
    return app

app = get_app()
