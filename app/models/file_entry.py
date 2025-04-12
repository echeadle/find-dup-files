# /home/echeadle/15_DupFiles/find-dup-files/app/models/file_entry.py
from sqlalchemy.orm import declarative_base  # Updated import for SQLAlchemy 2.0+
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class FileEntry(Base):
    __tablename__ = "files"  # Explicitly set table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, unique=True, index=True, nullable=False, doc="Absolute path to the file")
    hash = Column(String, index=True, nullable=False, doc="SHA-256 hash of the file content")
    size = Column(Integer, nullable=False, doc="Size of the file in bytes")
    mtime = Column(Float, nullable=False, doc="Last modification time (timestamp)")

    def __repr__(self):
        # Reason: Provide a helpful string representation for debugging.
        return f"<FileEntry(id={self.id}, path='{self.path}', hash='{self.hash[:8]}...')>"

