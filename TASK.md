# Duplicate File Finder - TASKS

## Initial Setup
- [x] Initialize Git repository
- [x] Set up Python virtual environment
- [x] Install FastAPI, Uvicorn, SQLite3 driver
- [x] Create initial project structure

## Core Functionality
- [x] Define SQLite schema: `files (id, path, hash, size, mtime)`
- [x] Implement directory walker
- [x] Skip symlinks
- [x] Hash files using SHA-256
- [x] Store/update file entries in database
- [x] Avoid re-hashing files with unchanged size+mtime
- [x] Detect duplicates by grouping hashes

## API Endpoints (FastAPI)
- [x] `POST /scan` - Trigger scan for specified path
- [x] `GET /files` - Return list of all scanned files
- [x] `GET /duplicates` - Return list of duplicate file groups

## Frontend (Simple Web Interface)
- [x] Create minimal HTML/JS UI (served via FastAPI)
- [x] Form to enter directory path and trigger scan
- [ ] Table to show duplicates grouped by hash
- [ ] Show scan status and error messages

## Testing
- [ ] Unit test for hash function and file scanner
- [ ] Integration tests for API endpoints
- [ ] Manual test for frontend scan & duplicate display

## Documentation
- [ ] README with setup + run instructions
- [ ] Include OpenAPI docs via FastAPI

## Discovered During Work
- [x] Upload repository to Git (GitHub, GitLab, etc.)
- [x] Create config file to exclude directories
- [ ] Create app/main.py file
