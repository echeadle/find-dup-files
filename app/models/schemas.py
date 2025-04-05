from pydantic import BaseModel

class FileEntrySchema(BaseModel):
    id: int
    path: str
    hash: str
    size: int
    mtime: float

    class Config:
        orm_mode = True