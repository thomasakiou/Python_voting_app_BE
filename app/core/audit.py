from sqlalchemy.orm import Session
from ..domain.audit_log import AuditLog
import logging

logger = logging.getLogger(__name__)

def record_audit_log(
    db: Session,
    admin_username: str,
    action: str,
    target_type: str = None,
    target_id: str = None,
    details: str = None,
    admin_id: int = None
):
    """Record an administrative action into the audit trail."""
    try:
        log_entry = AuditLog(
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            details=details
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        db.rollback()
