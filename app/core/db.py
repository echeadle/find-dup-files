from sqlmodel import SQLModel, create_engine, Session
from app.models.file_entry import FileEntry


def create_db_engine(db_file: str = "files.db"):
    """
    Creates a SQLite database engine.

    Args:
        db_file: The path to the database file.

    Returns:
        The database engine.
    """
    engine = create_engine(f"sqlite:///{db_file}")
    return engine


def create_db_and_tables(engine):
    """
    Creates the database and tables.

    Args:
        engine: The database engine.
    """
    SQLModel.metadata.create_all(engine)


def get_db_session(engine):
    """
    Creates a database session.

    Args:
        engine: The database engine.

    Returns:
        A database session.
    """
    with Session(engine) as session:
        yield session
