from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
import io
import csv
from datetime import datetime

from ..core import database, oauth2
from ..schemas import user as schemas
from ..core.config import settings
from ..core.database import get_db
from ..core.audit import record_audit_log
from ..core.cache import cache
from ..domain.user import User
from ..domain.vote import Vote
from ..domain import otp as otp_models
from ..application.commands.user.create_user import (
    CreateUserCommand,
    CreateUserHandler,
    ImportVotersCommand,
    ImportVotersHandler,
)
from ..application.commands.user.delete_user import DeleteUserCommand, DeleteUserHandler
from ..application.queries.user.get_all_users import ListUsersQuery, ListUsersHandler
from ..application.queries.user.get_user_by_username import GetUserByUsernameQuery, GetUserByUsernameHandler
from ..application.commands.user.toggle_active_user import ToggleUserStatusCommand, ToggleUserStatusHandler
from ..application.commands.user.disable_enable_voters import (
    DisableAllVotersCommand,
    DisableAllVotersHandler,
    EnableAllVotersCommand,
    EnableAllVotersHandler,
)

router = APIRouter(prefix=f"{settings.api_prefix}/users", tags=["Users"])


def apply_user_filters(
    query,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    accreditation: Optional[str] = None,
):
    if role and role != "all":
        query = query.filter(User.role == role)
    else:
        query = query.filter(User.role == "voter")

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.username.ilike(term),
                User.full_name.ilike(term),
                User.phone.ilike(term),
                User.email.ilike(term),
            )
        )

    if status and status != "all":
        if status == "active":
            query = query.filter(User.is_active == True)
        elif status == "inactive":
            query = query.filter(User.is_active == False)
        elif status == "eligible":
            query = query.filter(User.is_active == True, User.is_accredited == True)
        elif status == "ineligible":
            query = query.filter(or_(User.is_active == False, User.is_accredited == False))

    if accreditation and accreditation != "all":
        if accreditation == "accredited":
            query = query.filter(User.is_accredited == True)
        elif accreditation in ("pending", "unaccredited"):
            query = query.filter(User.is_accredited == False)

    return query


# ============================================================
# ANALYSIS OF ALL VOTERS (REQUIREMENT 3)
# ============================================================
@router.get("/stats/analysis", response_model=schemas.UserStatsOut)
def get_voters_analysis(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Returns complete breakdown of:
    all voters, all accredited voters, unaccredited voters, eligible & non-eligible voters,
    active & disabled voters, and total votes cast with turnout percentage.
    """
    cached = cache.get("voter_analysis")
    if cached:
        return cached

    # Optimized single aggregation query across all voters
    stats_row = db.query(
        func.count().filter(User.role == "voter").label("total_voters"),
        func.count().filter(User.role == "voter", User.is_accredited == True).label("accredited_voters"),
        func.count().filter(User.role == "voter", User.is_active == True).label("active_voters"),
        func.count().filter(User.role == "voter", User.is_active == False).label("disabled_voters"),
        func.count().filter(User.role == "voter", User.is_active == True, User.is_accredited == True).label("eligible_voters"),
    ).first()

    total_voters = (stats_row.total_voters if stats_row else 0) or 0
    accredited_voters = (stats_row.accredited_voters if stats_row else 0) or 0
    active_voters = (stats_row.active_voters if stats_row else 0) or 0
    disabled_voters = (stats_row.disabled_voters if stats_row else 0) or 0
    eligible_voters = (stats_row.eligible_voters if stats_row else 0) or 0
    unaccredited_voters = max(0, total_voters - accredited_voters)
    non_eligible_voters = max(0, total_voters - eligible_voters)

    # Optimized single query for total votes and unique voters
    vote_stats = db.query(
        func.count(Vote.id).label("total_votes"),
        func.count(func.distinct(Vote.user_id)).label("unique_voters")
    ).first()
    total_votes_cast = (vote_stats.total_votes if vote_stats else 0) or 0
    unique_voters_voted = (vote_stats.unique_voters if vote_stats else 0) or 0

    turnout_percentage = 0.0
    if accredited_voters > 0:
        turnout_percentage = round((unique_voters_voted / accredited_voters) * 100, 1)

    result = schemas.UserStatsOut(
        total_voters=total_voters,
        accredited_voters=accredited_voters,
        unaccredited_voters=unaccredited_voters,
        eligible_voters=eligible_voters,
        non_eligible_voters=non_eligible_voters,
        active_voters=active_voters,
        disabled_voters=disabled_voters,
        total_votes_cast=total_votes_cast,
        turnout_percentage=turnout_percentage,
    )
    cache.set("voter_analysis", result, ttl_seconds=15)
    return result


# ============================================================
# EXPORT ALL / FILTERED VOTERS AS CSV
# ============================================================
@router.get("/export/csv")
def export_voters_csv(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    accreditation: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download a CSV file containing voters matching the selected filters.
    """
    query = db.query(User)
    query = apply_user_filters(query, search=search, role=role, status=status, accreditation=accreditation)
    voters = query.order_by(User.username.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "MCS Number (Username)",
        "Full Name",
        "Phone Number",
        "Email Address",
        "Accredited",
        "Active",
        "Eligibility Status",
        "Date Accredited",
        "Registered At"
    ])

    for v in voters:
        is_eligible = v.is_active and v.is_accredited
        eligibility_label = "Eligible" if is_eligible else ("Disqualified" if not v.is_active else "Pending Accreditation")
        writer.writerow([
            v.username,
            v.full_name,
            v.phone or "",
            v.email or "",
            "YES" if v.is_accredited else "NO",
            "ACTIVE" if v.is_active else "DISABLED",
            eligibility_label,
            v.accredited_at.strftime("%Y-%m-%d %H:%M:%S") if v.accredited_at else "",
            v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else ""
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=neco_mcs_voters_list.csv"}
    )


# ============================================================
# EXPORT ALL / FILTERED VOTERS AS PDF
# ============================================================
@router.get("/export/pdf")
def export_voters_pdf(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    accreditation: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download a professional PDF document containing voters matching the selected filters.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation library 'reportlab' is missing. Please run 'pip install reportlab' on the server."
        )

    import html

    query = db.query(User)
    query = apply_user_filters(query, search=search, role=role, status=status, accreditation=accreditation)
    voters = query.order_by(User.username.asc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        alignment=1,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=15,
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
    )
    header_style = ParagraphStyle(
        'HCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
        leading=10,
    )

    story = []
    story.append(Paragraph("NECO MCS ELECTION - OFFICIAL VOTERS REGISTER", title_style))
    story.append(Paragraph(f"Export Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {len(voters)}", subtitle_style))

    data = [[
        Paragraph("MCS #", header_style),
        Paragraph("Full Name", header_style),
        Paragraph("Phone", header_style),
        Paragraph("Email", header_style),
        Paragraph("Accredited", header_style),
        Paragraph("Account Status", header_style),
        Paragraph("Eligibility", header_style),
    ]]

    for v in voters:
        is_eligible = v.is_active and v.is_accredited
        eligibility = "Eligible" if is_eligible else ("Disqualified" if not v.is_active else "Not Accredited")
        status_color = "#16a34a" if v.is_active else "#dc2626"
        accredited_color = "#16a34a" if v.is_accredited else "#eab308"

        username_safe = html.escape(str(v.username or ""))
        fullname_safe = html.escape(str(v.full_name or ""))
        phone_safe = html.escape(str(v.phone or "-"))
        email_safe = html.escape(str(v.email or "-"))

        data.append([
            Paragraph(username_safe, cell_style),
            Paragraph(fullname_safe, cell_style),
            Paragraph(phone_safe, cell_style),
            Paragraph(email_safe, cell_style),
            Paragraph(f"<font color='{accredited_color}'><b>{'YES' if v.is_accredited else 'NO'}</b></font>", cell_style),
            Paragraph(f"<font color='{status_color}'><b>{'ACTIVE' if v.is_active else 'DISABLED'}</b></font>", cell_style),
            Paragraph(eligibility, cell_style),
        ])

    table = Table(data, colWidths=[65, 140, 95, 170, 75, 90, 95])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))

    story.append(table)
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=neco_mcs_voters_list.pdf"}
    )


# ============================================================
# CREATE USER (ADMIN)
# ============================================================
@router.post("/admin", response_model=schemas.UserOut)
def create_admin_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin"])),
):
    command = CreateUserCommand(
        username=user.username,
        password=user.password or "admin123",
        full_name=user.full_name or user.username,
        phone=user.phone,
        email=user.email,
        role="admin",
        must_change_password=False,
    )
    handler = CreateUserHandler(db)
    created = handler.handle(command)
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="CREATE_ADMIN",
        target_type="ADMIN",
        target_id=str(created.username),
        details=f"Created admin user {created.username}",
        admin_id=current_user.id,
    )
    return created


# ============================================================
# CREATE USER (VOTER)
# ============================================================
@router.post("/voter", response_model=schemas.UserOut)
def create_voter_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = CreateUserCommand(
        username=user.username,
        password=user.password or "voter123",
        full_name=user.full_name or user.username,
        phone=user.phone,
        email=user.email,
        role="voter",
        must_change_password=True,
    )
    handler = CreateUserHandler(db)
    created = handler.handle(command)
    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="CREATE_VOTER",
        target_type="VOTER",
        target_id=str(created.username),
        details=f"Created voter user {created.username}",
        admin_id=current_user.id,
    )
    return created


# ============================================================
# UPLOAD USER-CSV (VOTER)
# ============================================================
@router.post("/upload-csv")
def upload_voters_csv(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed.",
        )

    try:
        contents = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}",
        )

    voters = []
    skipped_rows = []
    try:
        for row_idx, row in enumerate(reader, start=2):
            username = (row.get("username") or "").strip()
            # Skip empty or repeated header rows embedded in CSV
            if not username or username.lower() in ("username", "mcs_number", "mcs", "voter_id"):
                continue

            voters.append({
                "username": username,
                "full_name": (row.get("full_name") or row.get("fullName") or "").strip(),
                "phone": (row.get("phone") or row.get("phoneNo") or "").strip() or None,
                "email": (row.get("email") or "").strip() or None,
                "role": (row.get("role") or "voter").strip(),
                "password": (row.get("password") or "").strip(),
            })
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required column in CSV: {str(e)}",
        )

    command = ImportVotersCommand(voters=voters)
    handler = ImportVotersHandler(db)
    result = handler.handle(command)

    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="BULK_IMPORT_VOTERS",
        target_type="VOTERS",
        details=f"Imported {len(result['created'])} voters, skipped {len(result['skipped'])}",
        admin_id=current_user.id,
    )

    return {
        "created": len(result["created"]),
        "created_usernames": [u.username for u in result["created"]],
        "skipped": len(result["skipped"]),
        "skipped_details": result["skipped"],
    }


# ============================================================
# BULK DISQUALIFY VOTERS VIA CSV
# ============================================================
@router.post("/bulk-disqualify")
def bulk_disqualify_voters(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Upload a CSV containing voter usernames (MCS numbers) to disqualify them (set is_active = False).
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed.",
        )

    try:
        contents = file.file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}",
        )

    raw_usernames = []
    header_checked = False
    username_col_idx = 0

    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue

        if not header_checked:
            header_checked = True
            lowered = [col.strip().lower() for col in row]
            for idx, col in enumerate(lowered):
                if col in ("username", "mcs", "mcs_number", "voter_id", "mcs number"):
                    username_col_idx = idx
                    break
            if any(h in lowered for h in ("username", "mcs", "mcs_number", "full_name", "name", "voter_id")):
                continue

        if username_col_idx < len(row):
            val = row[username_col_idx].strip()
            if val and val.lower() not in ("username", "mcs", "mcs_number", "voter_id"):
                raw_usernames.append(val)

    if not raw_usernames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid usernames found in the uploaded CSV.",
        )

    unique_usernames = list(dict.fromkeys(raw_usernames))

    matched_users = (
        db.query(User)
        .filter(User.username.in_(unique_usernames))
        .all()
    )

    matched_usernames_set = {u.username for u in matched_users}
    not_found = [u for u in unique_usernames if u not in matched_usernames_set]

    disqualified_count = 0
    for u in matched_users:
        if u.role in ("admin", "super-admin"):
            continue
        u.is_active = False
        disqualified_count += 1

    db.commit()

    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="BULK_DISQUALIFY_VOTERS",
        target_type="VOTERS",
        details=f"Disqualified {disqualified_count} voters via CSV upload (not found: {len(not_found)})",
        admin_id=current_user.id,
    )

    return {
        "message": f"Successfully disqualified {disqualified_count} voter(s).",
        "disqualified_count": disqualified_count,
        "disqualified_usernames": [u.username for u in matched_users if u.role == "voter"],
        "not_found_count": len(not_found),
        "not_found_usernames": not_found,
    }


# ============================================================
# GET ALL USERS
# ============================================================
@router.get("/", response_model=List[schemas.UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    cached = cache.get("all_users_list")
    if cached is not None:
        return cached

    query = ListUsersQuery()
    handler = ListUsersHandler(db)
    users = handler.handle(query)
    cache.set("all_users_list", users, ttl_seconds=15)
    return users


# ============================================================
# GET USER BY USERNAME
# ============================================================
@router.get("/{username}", response_model=schemas.UserOut)
def get_user(
    username: str,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    if current_user.role == "voter":
        own_identifiers = {str(current_user.id), current_user.username}
        if username not in own_identifiers or (name is not None and name not in own_identifiers):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voters may only view their own profile.",
            )
        return current_user

    query = GetUserByUsernameQuery(username=name or username)
    handler = GetUserByUsernameHandler(db)
    return handler.handle(query)


# ============================================================
# DELETE USER BY ID
# ============================================================
@router.delete("/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin"])),
):
    command = DeleteUserCommand(user_id=id)
    handler = DeleteUserHandler(db)
    result = handler.handle(command)
    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="DELETE_USER",
        target_type="USER",
        target_id=str(id),
        details=f"Deleted user id {id}",
        admin_id=current_user.id,
    )
    return result


# ============================================================
# TOGGLE USER FIELD (is_active) - REQUIREMENT 3 & 5
# ============================================================
@router.patch("/{user_id}/status", response_model=schemas.UserOut)
def toggle_active_status(
    user_id: int,
    is_active: bool = Query(...),
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Disable or enable an individual voter. Any voter disabled by admin
    becomes a non-eligible voter and cannot log in to vote or accredit.
    """
    command = ToggleUserStatusCommand(
        user_id=user_id,
        is_active=is_active,
    )
    handler = ToggleUserStatusHandler(db)
    updated_user = handler.handle(command)

    cache.delete("voter_analysis")
    cache.delete("all_users_list")

    action_label = "ENABLE_USER" if is_active else "DISABLE_USER"
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action=action_label,
        target_type="USER",
        target_id=str(updated_user.username),
        details=f"Admin set is_active={is_active} for voter {updated_user.username} ({updated_user.full_name})",
        admin_id=current_user.id,
    )

    return updated_user


# ============================================================
# DISABLE ALL VOTERS
# ============================================================
@router.patch("/disable-voters")
def disable_all_voters(
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = DisableAllVotersCommand()
    handler = DisableAllVotersHandler(db)
    result = handler.handle(command)
    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="DISABLE_ALL_VOTERS",
        target_type="VOTERS",
        details="Disabled all voters",
        admin_id=current_user.id,
    )
    return result


# ============================================================
# ENABLE ALL VOTERS
# ============================================================
@router.patch("/enable-voters")
def enable_all_voters(
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    command = EnableAllVotersCommand()
    handler = EnableAllVotersHandler(db)
    result = handler.handle(command)
    cache.delete("voter_analysis")
    cache.delete("all_users_list")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="ENABLE_ALL_VOTERS",
        target_type="VOTERS",
        details="Enabled all voters",
        admin_id=current_user.id,
    )
    return result


# ============================================================
# REVERSE VOTER ACCREDITATION (ADMIN)
# ============================================================
@router.patch("/{user_id}/reverse-accreditation", response_model=schemas.UserOut)
@router.patch("/{user_id}/reverse-accreditation/", response_model=schemas.UserOut)
@router.post("/{user_id}/reverse-accreditation", response_model=schemas.UserOut)
@router.post("/{user_id}/reverse-accreditation/", response_model=schemas.UserOut)
def reverse_voter_accreditation(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Reverse accreditation for a voter so they can undergo accreditation again.
    Resets is_accredited to False, clears accredited_at, and invalidates active OTPs.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with ID {user_id} not found.",
        )

    if user.role != "voter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accreditation can only be reversed for voter accounts.",
        )

    # Check if voter has already cast votes in this election
    has_voted = db.query(Vote).filter(Vote.user_id == user.id).first()
    if has_voted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reverse accreditation for voter '{user.username}' because they have already cast votes in this election.",
        )

    if not user.is_accredited:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voter '{user.username}' ({user.full_name}) is not currently accredited.",
        )

    # Invalidate all prior accreditation OTPs
    db.query(otp_models.OTP).filter(
        otp_models.OTP.user_id == user.id,
        otp_models.OTP.purpose == "accreditation",
    ).update({"is_used": True})

    # Reset accreditation fields and release device lock
    user.is_accredited = False
    user.accredited_at = None
    user.accredited_device_id = None
    user.device_info = None
    db.commit()
    db.refresh(user)

    cache.delete("voter_analysis")
    cache.delete("all_users_list")

    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="REVERSE_ACCREDITATION",
        target_type="VOTER",
        target_id=str(user.username),
        details=f"Admin reversed accreditation for voter {user.username} ({user.full_name}) to allow re-accreditation",
        admin_id=current_user.id,
    )

    return user


@router.patch("/username/{username}/reverse-accreditation", response_model=schemas.UserOut)
@router.patch("/username/{username}/reverse-accreditation/", response_model=schemas.UserOut)
@router.post("/username/{username}/reverse-accreditation", response_model=schemas.UserOut)
@router.post("/username/{username}/reverse-accreditation/", response_model=schemas.UserOut)
def reverse_voter_accreditation_by_username(
    username: str,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Reverse accreditation by voter MCS username.
    """
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with MCS number '{username}' not found.",
        )
    return reverse_voter_accreditation(user_id=user.id, db=db, current_user=current_user)
