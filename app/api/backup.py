import os
import shutil
from datetime import datetime
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/system", tags=["System Backup"])

BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backups"))
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "automation_engine.db"))


@router.post("/backup")
def backup_database():
    """
    Creates a timestamped backup copy of the local SQLite database into backups/ directory.
    """
    if not os.path.exists(DB_FILE):
        raise HTTPException(status_code=404, detail="Database file automation_engine.db not found.")

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_filename = f"automation_engine_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copy2(DB_FILE, backup_path)
        file_size_bytes = os.path.getsize(backup_path)
        return {
            "status": "success",
            "message": f"Database backup created successfully: {backup_filename}",
            "backup_path": backup_path,
            "filename": backup_filename,
            "size_bytes": file_size_bytes,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create database backup: {str(e)}")
