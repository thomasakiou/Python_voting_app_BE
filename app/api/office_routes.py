from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core import database, oauth2
from ..schemas import office as schemas
from ..core.config import settings
from ..core.database import get_db
from ..core.audit import record_audit_log
from ..core.cache import cache
from ..domain.office import Office
from ..application.commands.office.create_office import CreateOfficeCommand, CreateOfficeHandler
from ..application.commands.office.delete_office import DeleteOfficeCommand, DeleteOfficeHandler
from ..application.commands.office.update_office import UpdateOfficeCommand, UpdateOfficeHandler
from ..application.queries.office.get_all_offices import ListOfficesQuery, ListOfficesHandler
from ..application.queries.office.get_office_by_code import GetOfficeByCodeQuery, GetOfficeByCodeHandler

router = APIRouter(prefix=f"{settings.api_prefix}/offices", tags=["Offices"])


# ==========================
# CREATE OFFICE
# ==========================
@router.post("/", response_model=schemas.OfficeResponse)
def create_office(
    office: schemas.OfficeCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = CreateOfficeCommand(
        office_code=office.office_code,
        description=office.description,
        max_votes=office.max_votes if office.max_votes is not None else 1,
    )
    handler = CreateOfficeHandler(db)
    result = handler.handle(command)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="CREATE_OFFICE",
        target_type="OFFICE",
        target_id=office.office_code,
        details=f"Created office {office.description} ({office.office_code})",
        admin_id=current_user.id,
    )
    return result


# ==========================
# GET ALL OFFICES
# ==========================
@router.get("/", response_model=List[schemas.OfficeResponse])
def get_all_offices(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    query = ListOfficesQuery()
    handler = ListOfficesHandler(db)
    return handler.handle(query)


# ======================================
# GET OFFICE BY CODE
# ======================================
@router.get("/{office_code}", response_model=schemas.OfficeResponse)
def get_office_by_code(
    office_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    query = GetOfficeByCodeQuery(office_code=office_code)
    handler = GetOfficeByCodeHandler(db)
    return handler.handle(query)


# ======================================
# DISQUALIFY / QUALIFY OFFICE (ADMIN)
# ======================================
@router.patch("/{id}/disqualify", response_model=schemas.OfficeResponse)
def toggle_office_disqualification(
    id: int,
    payload: schemas.OfficeDisqualifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    office = db.query(Office).filter(Office.id == id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")

    office.is_disqualified = payload.is_disqualified
    db.commit()
    db.refresh(office)

    action_label = "DISQUALIFY_OFFICE" if payload.is_disqualified else "QUALIFY_OFFICE"
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action=action_label,
        target_type="OFFICE",
        target_id=str(office.office_code),
        details=f"Admin set is_disqualified={payload.is_disqualified} for {office.description}",
        admin_id=current_user.id,
    )
    cache.clear()
    return office


# ==========================
# DELETE OFFICE BY ID
# ==========================
@router.delete("/{id}")
def delete_office(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = DeleteOfficeCommand(office_id=id)
    handler = DeleteOfficeHandler(db)
    result = handler.handle(command)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="DELETE_OFFICE",
        target_type="OFFICE",
        target_id=str(id),
        details=f"Deleted office id {id}",
        admin_id=current_user.id,
    )
    return result


# ==========================
# UPDATE OFFICE BY ID
# ==========================
@router.put("/{id}", response_model=schemas.OfficeResponse)
def update_office(
    id: int,
    office: schemas.OfficeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = UpdateOfficeCommand(
        office_id=id,
        office_code=office.office_code,
        description=office.description,
        max_votes=office.max_votes,
    )
    handler = UpdateOfficeHandler(db)
    result = handler.handle(command)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="UPDATE_OFFICE",
        target_type="OFFICE",
        target_id=str(id),
        details=f"Updated office {office.description}",
        admin_id=current_user.id,
    )
    return result
