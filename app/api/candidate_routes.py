import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List

from ..core import database, oauth2
from ..schemas import candidate as schemas
from ..core.config import settings
from ..core.database import get_db
from ..core.audit import record_audit_log
from ..core.cache import cache
from ..domain.candidate import Candidate
from ..domain.user import User
from ..application.commands.candidate.create_candidate import CreateCandidateCommand, CreateCandidateHandler
from ..application.queries.candidate.get_all_candidates import ListCandidatesHandler, ListCandidatesQuery
from ..application.queries.candidate.get_candidate_by_code import GetCandidateByCodeQuery, GetCandidateByCodeHandler
from ..application.queries.candidate.get_candidate_by_office_code import GetCandidateByOfficeCodeQuery, GetCandidateByOfficeCodeHandler
from ..application.commands.candidate.delete_candidate import DeleteCandidateCommand, DeleteCandidateHandler
from ..application.commands.candidate.update_candidate import UpdateCandidateCommand, UpdateCandidateHandler

router = APIRouter(prefix=f"{settings.api_prefix}/candidates", tags=["Candidates"])


def enrich_candidate(cand: Candidate, db: Session) -> Candidate:
    """
    Enriches candidate with staff information from User (voters) table.
    Matches candidate_code to User.username, extracting MCS number, file number, CONRAISS, and station.
    """
    if not cand:
        return cand

    user = None
    # 1. Primary match: Match User.username to candidate_code (MCS Number is equal to candidate_code)
    if cand.candidate_code:
        code_clean = cand.candidate_code.strip()
        user = db.query(User).filter(
            or_(
                User.username == code_clean,
                func.lower(User.username) == func.lower(code_clean)
            )
        ).first()

    # 2. Secondary match: if not found, match by cand.mcs_number
    if not user and cand.mcs_number:
        mcs_clean = cand.mcs_number.strip()
        user = db.query(User).filter(
            or_(
                User.username == mcs_clean,
                func.lower(User.username) == func.lower(mcs_clean)
            )
        ).first()

    # 3. Tertiary match: if not found, match by full name
    if not user and cand.name:
        name_clean = cand.name.strip()
        user = db.query(User).filter(
            or_(
                func.lower(User.full_name) == func.lower(name_clean),
                User.full_name.ilike(f"%{name_clean}%"),
            )
        ).first()

    if user:
        if not cand.mcs_number or cand.mcs_number.strip() == '':
            cand.mcs_number = user.username or cand.candidate_code
        if not cand.conraiss and user.staff_conraiss:
            cand.conraiss = user.staff_conraiss
        if not cand.station and user.staff_station:
            cand.station = user.staff_station
        if not cand.file_no and user.staff_file_no:
            cand.file_no = user.staff_file_no
    else:
        # Fallback: candidate_code is MCS Number
        if not cand.mcs_number or cand.mcs_number.strip() == '':
            cand.mcs_number = cand.candidate_code

    return cand


# ==========================
# CREATE CANDIDATES
# ==========================
@router.post("/", response_model=schemas.CandidateResponse)
def create_candidate(
    candidate: schemas.CandidateCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    mcs_number = candidate.mcs_number
    conraiss = candidate.conraiss
    station = candidate.station
    file_no = candidate.file_no

    # Auto-resolve from User table by matching candidate_code to User.username
    user = None
    code_clean = candidate.candidate_code.strip() if candidate.candidate_code else ""
    if code_clean:
        user = db.query(User).filter(
            or_(
                User.username == code_clean,
                func.lower(User.username) == func.lower(code_clean)
            )
        ).first()
    if not user and mcs_number:
        user = db.query(User).filter(
            or_(
                User.username == mcs_number.strip(),
                func.lower(User.username) == func.lower(mcs_number.strip())
            )
        ).first()
    if not user and candidate.name:
        user = db.query(User).filter(func.lower(User.full_name) == func.lower(candidate.name.strip())).first()

    if user:
        mcs_number = user.username or mcs_number or candidate.candidate_code
        conraiss = conraiss or user.staff_conraiss
        station = station or user.staff_station
        file_no = file_no or user.staff_file_no
    else:
        if not mcs_number:
            mcs_number = candidate.candidate_code

    command = CreateCandidateCommand(
        candidate_code=candidate.candidate_code,
        name=candidate.name,
        office_code=candidate.office_code,
        image_url=candidate.image_url,
        manifesto_title=candidate.manifesto_title,
        manifesto=candidate.manifesto,
        mcs_number=mcs_number,
        conraiss=conraiss,
        station=station,
        file_no=file_no,
    )
    handler = CreateCandidateHandler(db)
    result = handler.handle(command)
    enrich_candidate(result, db)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="CREATE_CANDIDATE",
        target_type="CANDIDATE",
        target_id=candidate.candidate_code,
        details=f"Created candidate {candidate.name} ({candidate.candidate_code}) for office {candidate.office_code}",
        admin_id=current_user.id,
    )
    return result


# ==========================
# GET ALL CANDIDATES
# ==========================
@router.get("/", response_model=List[schemas.CandidateResponse])
def get_all_candidates(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    query = ListCandidatesQuery()
    handler = ListCandidatesHandler(db)
    candidates = handler.handle(query)
    for c in candidates:
        enrich_candidate(c, db)
    return candidates


# ======================================
# GET CANDIDATE BY OFFICE CODE
# ======================================
@router.get("/{office_code}/candidates", response_model=List[schemas.CandidateResponse])
def get_candidates_by_office_code(
    office_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    query = GetCandidateByOfficeCodeQuery(office_code=office_code)
    handler = GetCandidateByOfficeCodeHandler(db)
    candidates = handler.handle(query)
    for c in candidates:
        enrich_candidate(c, db)
    return candidates


# ==========================
# GET CANDIDATES BY CODE
# ==========================
@router.get("/{candidate_code}", response_model=schemas.CandidateResponse)
def get_candidate_by_code(
    candidate_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    query = GetCandidateByCodeQuery(candidate_code=candidate_code)
    handler = GetCandidateByCodeHandler(db)
    cand = handler.handle(query)
    if not cand or (getattr(cand, "is_hidden", False) and current_user.role not in ["super-admin", "admin"]):
        raise HTTPException(status_code=404, detail="Candidate not found")
    enrich_candidate(cand, db)
    return cand


# ======================================
# DISQUALIFY / QUALIFY CANDIDATE (ADMIN)
# ======================================
@router.patch("/{id}/disqualify", response_model=schemas.CandidateResponse)
def toggle_candidate_disqualification(
    id: int,
    payload: schemas.CandidateDisqualifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.is_disqualified = payload.is_disqualified
    db.commit()
    db.refresh(candidate)

    action_label = "DISQUALIFY_CANDIDATE" if payload.is_disqualified else "QUALIFY_CANDIDATE"
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action=action_label,
        target_type="CANDIDATE",
        target_id=str(candidate.candidate_code),
        details=f"Admin set is_disqualified={payload.is_disqualified} for {candidate.name}",
        admin_id=current_user.id,
    )
    cache.clear()
    return candidate


# ======================================
# HIDE / UNHIDE CANDIDATE (ADMIN ONLY)
# ======================================
@router.patch("/{id}/hide", response_model=schemas.CandidateResponse)
def toggle_candidate_visibility(
    id: int,
    payload: schemas.CandidateHideRequest,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.is_hidden = payload.is_hidden
    db.commit()
    db.refresh(candidate)

    action_label = "HIDE_CANDIDATE" if payload.is_hidden else "UNHIDE_CANDIDATE"
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action=action_label,
        target_type="CANDIDATE",
        target_id=str(candidate.candidate_code),
        details=f"Admin set is_hidden={payload.is_hidden} for {candidate.name}",
        admin_id=current_user.id,
    )
    cache.clear()
    return candidate


# ==========================
# DELETE CANDIDATE BY ID
# ==========================
@router.delete("/{id}")
def delete_candidate(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = DeleteCandidateCommand(candidate_id=id)
    handler = DeleteCandidateHandler(db)
    result = handler.handle(command)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="DELETE_CANDIDATE",
        target_type="CANDIDATE",
        target_id=str(id),
        details=f"Deleted candidate id {id}",
        admin_id=current_user.id,
    )
    return result


# ==========================
# UPDATE CANDIDATE BY ID
# ==========================
@router.put("/{id}", response_model=schemas.CandidateResponse)
def update_candidate(
    id: int,
    candidate: schemas.CandidateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    mcs_number = candidate.mcs_number
    conraiss = candidate.conraiss
    station = candidate.station
    file_no = candidate.file_no

    # Auto-resolve from User table by matching candidate_code to User.username
    user = None
    code_clean = candidate.candidate_code.strip() if candidate.candidate_code else ""
    if code_clean:
        user = db.query(User).filter(
            or_(
                User.username == code_clean,
                func.lower(User.username) == func.lower(code_clean)
            )
        ).first()
    if not user and mcs_number:
        user = db.query(User).filter(
            or_(
                User.username == mcs_number.strip(),
                func.lower(User.username) == func.lower(mcs_number.strip())
            )
        ).first()
    if not user and candidate.name:
        user = db.query(User).filter(func.lower(User.full_name) == func.lower(candidate.name.strip())).first()

    if user:
        mcs_number = mcs_number or user.username or candidate.candidate_code
        conraiss = conraiss or user.staff_conraiss
        station = station or user.staff_station
        file_no = file_no or user.staff_file_no
    else:
        if not mcs_number:
            mcs_number = candidate.candidate_code

    command = UpdateCandidateCommand(
        candidate_id=id,
        candidate_code=candidate.candidate_code,
        name=candidate.name,
        office_code=candidate.office_code,
        image_url=candidate.image_url,
        manifesto_title=candidate.manifesto_title,
        manifesto=candidate.manifesto,
        mcs_number=mcs_number,
        conraiss=conraiss,
        station=station,
        file_no=file_no,
    )
    handler = UpdateCandidateHandler(db)
    result = handler.handle(command)
    enrich_candidate(result, db)
    cache.clear()
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="UPDATE_CANDIDATE",
        target_type="CANDIDATE",
        target_id=str(id),
        details=f"Updated candidate {candidate.name}",
        admin_id=current_user.id,
    )
    return result


# ======================================
# UPLOAD CANDIDATE IMAGE
# ======================================
@router.post("/upload-image")
async def upload_candidate_image(
    file: UploadFile = File(...),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """Uploads a candidate portrait image and returns its URL."""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPG, PNG, WEBP",
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 5MB limit",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    filename = f"cand_{uuid.uuid4().hex[:12]}{ext}"
    upload_dir = os.path.join("uploads", "candidates")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Return URL routed through candidates router so Nginx reverse proxies it cleanly
    return {"image_url": f"/candidates/images/{filename}"}


# ======================================
# PUBLIC CANDIDATE IMAGE SERVING
# ======================================
@router.get("/images/{filename}")
def serve_candidate_image(filename: str):
    """
    Publicly serves candidate portrait image files.
    Allows browsers to load images via <img src="..." /> without authentication tokens.
    """
    safe_name = os.path.basename(filename)
    candidates_dir = os.path.join("uploads", "candidates")
    file_path = os.path.join(candidates_dir, safe_name)
    if not os.path.exists(file_path):
        # Fallback to root uploads folder
        file_path = os.path.join("uploads", safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Candidate image not found")

    ext = os.path.splitext(safe_name)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_types.get(ext, "image/jpeg")
    return FileResponse(file_path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/uploads/candidates/{filename}")
def serve_candidate_upload_path_image(filename: str):
    """Alias for candidates with legacy /uploads/candidates/... image paths."""
    return serve_candidate_image(filename)


# ======================================
# UPLOAD IMAGE FOR EXISTING CANDIDATE
# ======================================
@router.post("/{id}/image", response_model=schemas.CandidateResponse)
async def upload_candidate_image_by_id(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """Uploads and saves the image directly for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    res = await upload_candidate_image(file=file, current_user=current_user)
    candidate.image_url = res["image_url"]
    db.commit()
    db.refresh(candidate)
    cache.clear()
    return candidate
