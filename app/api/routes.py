# /home/echeadle/15_DupFiles/find-dup-files/app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict
from pathlib import Path
from typing import List, Dict

# Updated imports
from app.core.db import get_db_session
from app.core.scanner import scan_directory, find_duplicates # Import find_duplicates from scanner
from app.models.file_entry import FileEntry as DBFileEntry # Rename to avoid conflict

router = APIRouter()

class ScanRequest(BaseModel):
    """Request model for triggering a directory scan."""
    directory_path: str = Field(..., description="The absolute path to the directory to scan.")

class ScanResponse(BaseModel):
    """Response model for the scan endpoint."""
    message: str

class FileEntry(BaseModel):
    """Response model for a single file entry."""
    id: int
    path: str
    hash: str
    size: int
    mtime: float

    # Use ConfigDict for Pydantic V2 compatibility
    model_config = ConfigDict(from_attributes=True)


@router.post("/api/scan", response_model=ScanResponse, status_code=200)
async def trigger_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session)
):
    """
    Triggers a background scan of the specified directory.

    Args:
        scan_request (ScanRequest): The request body containing the directory path.
        background_tasks (BackgroundTasks): FastAPI background task manager.
        session (Session): Database session dependency.

    Returns:
        ScanResponse: A message indicating the scan has started or completed.

    Raises:
        HTTPException: 404 if the directory is not found.
    """
    scan_path = Path(scan_request.directory_path)
    if not scan_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {scan_path}")

    # Run the scan synchronously for simplicity in this version
    # For long scans, background_tasks.add_task(scan_directory, scan_path, session) is better
    try:
        # Correct argument order
        scan_directory(scan_path, session)
        return ScanResponse(message=f"Scan of directory '{scan_path}' completed.")
    except Exception as e:
        # Log the exception e
        print(f"Error during scan: {e}") # Basic logging
        raise HTTPException(status_code=500, detail=f"An error occurred during the scan: {str(e)}")


@router.get("/api/files", response_model=List[FileEntry])
async def get_all_files(session: Session = Depends(get_db_session)):
    """
    Retrieves a list of all files currently stored in the database.

    Args:
        session (Session): Database session dependency.

    Returns:
        List[FileEntry]: A list of file entries.
    """
    files = session.query(DBFileEntry).all()
    return files


@router.get("/api/duplicates", response_model=Dict[str, List[str]])
async def get_duplicates(session: Session = Depends(get_db_session)):
    """
    Retrieves a dictionary of duplicate files, grouped by hash.

    Args:
        session (Session): Database session dependency.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are file hashes
                               and values are lists of paths for duplicate files.
    """
    # Call the find_duplicates function imported from scanner.py
    duplicates = find_duplicates(session)
    return duplicates

