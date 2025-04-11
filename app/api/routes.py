from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.core.scanner import scan_directory
from pydantic import BaseModel
from pathlib import Path
from sqlalchemy import func
from app.core.config import read_config, update_config

# Create an APIRouter instance to handle API routes.
router = APIRouter()

# Define a Pydantic model for the scan request payload.
class ScanRequest(BaseModel):
    directory: str

# Define a Pydantic model for the config request payload.
class ConfigRequest(BaseModel):
    excluded_directories: list[str]

# Define the POST /scan endpoint.
@router.post("/scan")
async def scan(scan_request: ScanRequest, db: Session = Depends(get_db_session)):
    """
    Triggers a scan of the specified directory.

    Args:
        scan_request (ScanRequest): The request body containing the directory to scan.
        db (Session): The database session.

    Returns:
        dict: A message indicating the scan has been initiated.

    Raises:
        HTTPException: If the directory path is invalid or the scan fails.
    """
    # Convert the directory string to a Path object.
    directory_path = Path(scan_request.directory)

    # Check if the provided path is a valid directory.
    if not directory_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found.")

    try:
        # Call the scan_directory function to perform the scan.
        scan_directory(directory_path, db)
        return {"message": f"Scan of directory '{scan_request.directory}' completed."}
    except Exception as e:
        # Raise an HTTPException if the scan fails.
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# Define the GET /files endpoint.
@router.get("/files")
async def get_files(db: Session = Depends(get_db_session)):
    """
    Returns a list of all scanned files.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of FileEntry objects representing the scanned files.
    """
    from app.models.file_entry import FileEntry
    # Query the database for all FileEntry objects.
    files = db.query(FileEntry).all()
    return files

# Define the GET /duplicates endpoint.
@router.get("/duplicates")
async def get_duplicates(db: Session = Depends(get_db_session)):
    """
    Returns a list of duplicate file groups.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of FileEntry objects representing the duplicate files.
    """
    from app.models.file_entry import FileEntry
    # Query the database for FileEntry objects with duplicate hashes.
    duplicate_groups = []
    duplicate_hashes = db.query(FileEntry.hash).group_by(FileEntry.hash).having(func.count(FileEntry.hash) > 1).all()
    duplicate_hashes = [hash[0] for hash in duplicate_hashes]
    for hash in duplicate_hashes:
        duplicate_groups.append(db.query(FileEntry).filter_by(hash=hash).all())
    
    duplicate_list = []
    for group in duplicate_groups:
        for item in group:
            duplicate_list.append({"path": item.path})
    return duplicate_list

# Define the GET /config endpoint.
@router.get("/config")
async def get_config():
    """
    Returns the current configuration.
    """
    return read_config()

# Define the PUT /config endpoint.
@router.put("/config")
async def update_config_endpoint(config_request: ConfigRequest):
    """
    Updates the configuration.
    """
    update_config(config_request.model_dump())
    return {"message": "Configuration updated successfully."}
