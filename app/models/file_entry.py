from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileEntry(Base):
    __tablename__ = "file_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, index=True, nullable=False, doc="Absolute path to the file")
    hash = Column(String, index=True, nullable=False, doc="SHA-256 hash of the file content")
    size = Column(Integer, nullable=False, doc="Size of the file in bytes")
    mtime = Column(Float, nullable=False, doc="Last modification time (timestamp)")
