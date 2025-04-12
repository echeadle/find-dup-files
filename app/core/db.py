from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker, Session
from app.models.file_entry import Base, FileEntry # Import FileEntry model
from typing import Dict, List

def create_db_engine(db_file: str = "files.db"):
    """
    Creates a SQLite database engine.

    Args:
        db_file (str): The path to the database file. Defaults to "files.db".

    Returns:
        sqlalchemy.engine.Engine: The database engine.
    """
    # connect_args is specific to SQLite to allow multi-threaded access (like from FastAPI)
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    return engine


def create_db_and_tables(engine):
    """
    Creates the database and tables defined in the Base metadata.

    Args:
        engine (sqlalchemy.engine.Engine): The database engine.
    """
    Base.metadata.create_all(engine)


def get_db_session(engine):
    """
    Provides a database session context manager.

    Args:
        engine (sqlalchemy.engine.Engine): The database engine.

    Yields:
        Session: A SQLAlchemy Session object.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# --- Add this function ---
def find_duplicates_in_db(session: Session) -> Dict[str, List[str]]:
    """
    Finds duplicate files in the database by grouping identical hashes.

    Args:
        session (Session): The database session to use for querying.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are file hashes
                              and values are lists of paths for duplicate files.
                              Only includes hashes that appear more than once.
    """
    duplicates_dict = {}

    # Step 1: Find hashes that appear more than once
    subquery = (
        select(FileEntry.hash)
        .group_by(FileEntry.hash)
        .having(func.count(FileEntry.id) > 1)
        .subquery()
    )

    # Step 2: Select all file entries whose hash is in the subquery result
    stmt = select(FileEntry).where(FileEntry.hash.in_(select(subquery.c.hash)))

    duplicate_entries = session.execute(stmt).scalars().all()

    # Step 3: Group the paths by hash
    for entry in duplicate_entries:
        if entry.hash not in duplicates_dict:
            duplicates_dict[entry.hash] = []
        duplicates_dict[entry.hash].append(entry.path)

    return duplicates_dict
# --- End of added function ---

