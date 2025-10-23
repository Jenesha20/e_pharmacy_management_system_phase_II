from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import os
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_admin
from app.models.models import Backup, Restore, Customer
from app.schemas.admin import BackupCreate, RestoreCreate

router = APIRouter(prefix="/admin/backup", tags=["admin-backup"])

@router.post("/create")
def create_backup(
    backup_data: BackupCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a manual backup"""
    try:
        # Generate backup ID
        backup_id = f"BK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup directory if it doesn't exist
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # File path
        file_name = f"{backup_id}.json"
        file_path = os.path.join(backup_dir, file_name)
        
        # Create backup data structure
        backup_content = {
            "backup_id": backup_id,
            "created_at": datetime.now().isoformat(),
            "created_by": current_admin.customer_id,
            "type": backup_data.type,
            "data": backup_data.data_list
        }
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(backup_content, f, indent=2)
        
        # Save to database
        backup = Backup(
            backup_id=backup_id,
            file_name=file_name,
            path=file_path,
            type=backup_data.type,
            data_list=backup_data.data_list
        )
        db.add(backup)
        db.commit()
        
        return {
            "message": "Backup created successfully",
            "backup_id": backup_id,
            "file_path": file_path,
            "created_at": datetime.now()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )

@router.post("/restore")
def restore_backup(
    restore_data: RestoreCreate,
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Restore from a backup"""
    try:
        # Check if backup file exists
        if not os.path.exists(restore_data.path):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Read backup file
        with open(restore_data.path, 'r') as f:
            backup_content = json.load(f)
        
        # Generate restore ID
        restore_id = f"RS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save restore record to database
        restore = Restore(
            restore_id=restore_id,
            file_name=os.path.basename(restore_data.path),
            path=restore_data.path,
            type=restore_data.type,
            data_list=backup_content.get('data', {})
        )
        db.add(restore)
        db.commit()
        
        return {
            "message": "Restore process initiated successfully",
            "restore_id": restore_id,
            "backup_data": backup_content,
            "restored_at": datetime.now()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Restore process failed: {str(e)}"
        )

@router.get("/list")
def list_backups(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all available backups"""
    backups = db.query(Backup).order_by(Backup.date.desc()).all()
    
    return {
        "backups": [
            {
                "backup_id": backup.backup_id,
                "file_name": backup.file_name,
                "path": backup.path,
                "type": backup.type,
                "date": backup.date,
                "data_count": len(backup.data_list) if backup.data_list else 0
            }
            for backup in backups
        ]
    }

@router.get("/list-restores")
def list_restores(
    current_admin: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all restore operations"""
    restores = db.query(Restore).order_by(Restore.date.desc()).all()
    
    return {
        "restores": [
            {
                "restore_id": restore.restore_id,
                "file_name": restore.file_name,
                "path": restore.path,
                "type": restore.type,
                "date": restore.date,
                "data_count": len(restore.data_list) if restore.data_list else 0
            }
            for restore in restores
        ]
    }