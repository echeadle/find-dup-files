from typing import Optional
from sqlmodel import Field, SQLModel


class FileEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, description="Absolute path to the file")
    hash: str = Field(index=True, description="SHA-256 hash of the file content")
    size: int = Field(description="Size of the file in bytes")
    mtime: float = Field(description="Last modification time (timestamp)")
