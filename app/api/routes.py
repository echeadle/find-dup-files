from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.core.db import get_db_session
from app.core.scanner import scan_directory, find_duplicates
from app.models.file_entry import FileEntry 
from typing import List

router = APIRouter(prefix="/api")


class ScanRequest(BaseModel):
    directory: str


class ScanResponse(BaseModel):
    message: str


@router.post("/scan", response_model=ScanResponse)
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
        return ScanResponse(message=f"Scan of directory '{scan_request.directory}' completed.")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Directory '{scan_request.directory}' not found."
        )
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied to access directory '{scan_request.directory}'.",
        )
    except OSError as e:
        raise HTTPException(
            status_code=500, detail=f"OS error occurred during the scan: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during the scan: {e}"
        )


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


@router.get("/duplicates", response_model=List[List[FileEntry]])
def get_duplicates(session: Session = Depends(get_db_session)):
    """
    Returns a list of duplicate file groups.

    Args:
        session: The database session.

    Returns:
        A list of lists, where each inner list contains FileEntry objects
        that are duplicates of each other.
    """
    duplicate_groups = find_duplicates(session)
    return duplicate_groups
