from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.core.db import get_db_session
from app.core.scanner import scan_directory
from app.models.file_entry import FileEntry
from typing import List

router = APIRouter()


class ScanRequest(BaseModel):
    directory: str


@router.post("/scan")
def scan(scan_request: ScanRequest, session: Session = Depends(get_db_session)):
    """
    Triggers a scan of the specified directory.

    Args:
        scan_request: The request body containing the directory to scan.
        session: The database session.

    Returns:
        A success message.
    """
    try:
        scan_directory(scan_request.directory, session)
        return {"message": f"Scan of directory '{scan_request.directory}' completed."}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory '{scan_request.directory}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the scan: {e}")


@router.get("/files", response_model=List[FileEntry])
def get_files(session: Session = Depends(get_db_session)):
    """
    Returns a list of all scanned files.

    Args:
        session: The database session.

    Returns:
        A list of FileEntry objects.
    """
    statement = select(FileEntry)
    files = session.exec(statement).all()
    return files
