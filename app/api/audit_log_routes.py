from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import csv

from ..core import database, oauth2
from ..core.config import settings
from ..core.database import get_db
from ..domain.audit_log import AuditLog
from ..schemas import audit_log as schemas

router = APIRouter(prefix=f"{settings.api_prefix}/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=List[schemas.AuditLogOut])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Get audit trail logs of all admin changes.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return logs


@router.get("/export/csv")
def export_audit_logs_csv(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download complete audit log as a CSV file.
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Admin Username", "Action", "Target Type", "Target ID", "Details"])

    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            log.admin_username,
            log.action,
            log.target_type or "",
            log.target_id or "",
            log.details or ""
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
