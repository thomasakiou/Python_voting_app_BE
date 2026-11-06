from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
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

    # Voters count
    total_voters = db.query(User).filter(User.role == "voter").count()
    accredited_voters = db.query(User).filter(User.role == "voter", User.is_accredited == True).count()
    unaccredited_voters = total_voters - accredited_voters

    active_voters = db.query(User).filter(User.role == "voter", User.is_active == True).count()
    disabled_voters = db.query(User).filter(User.role == "voter", User.is_active == False).count()

    # Eligible voters are both active and accredited
    eligible_voters = db.query(User).filter(
        User.role == "voter",
        User.is_active == True,
        User.is_accredited == True
    ).count()

    # Non-eligible voters are either disabled OR unaccredited
    non_eligible_voters = total_voters - eligible_voters

    # Votes cast
    total_votes_cast = db.query(Vote).count()

    # Unique voters who cast at least one vote
    unique_voters_voted = db.query(func.count(func.distinct(Vote.user_id))).scalar() or 0

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
    cache.set("voter_analysis", result, ttl_seconds=5)
    return result


# ============================================================
# EXPORT ALL VOTERS AS CSV (REQUIREMENT 3)
# ============================================================
@router.get("/export/csv")
def export_voters_csv(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download a CSV file containing all voters and their accreditation/eligibility statuses.
    """
    voters = (
        db.query(User)
        .filter(User.role == "voter")
        .order_by(User.username.asc())
        .all()
    )

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
# EXPORT ALL VOTERS AS PDF (REQUIREMENT 3)
# ============================================================
@router.get("/export/pdf")
def export_voters_pdf(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download a professional PDF document containing all voters and their statuses.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation library 'reportlab' is missing. Please run 'pip install reportlab' on the server."
        )

    import html

    voters = (
        db.query(User)
        .filter(User.role == "voter")
        .order_by(User.username.asc())
        .all()
    )

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
    story.append(Paragraph(f"Export Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Voters: {len(voters)}", subtitle_style))

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
        password=user.password,
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
        target_type="USER",
        target_id=created.username,
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
        password=user.password,
        full_name=user.full_name or user.username,
        phone=user.phone,
        email=user.email,
        role="voter",
        must_change_password=True,
    )
    handler = CreateUserHandler(db)
    created = handler.handle(command)
    cache.delete("voter_analysis")
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="CREATE_VOTER",
        target_type="VOTER",
        target_id=created.username,
        details=f"Created voter {created.username} ({created.full_name})",
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
        contents = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}",
        )

    voters = []
    try:
        for row in reader:
            username = row.get("username", "").strip()
            if not username:
                continue

            voters.append({
                "username": username,
                "full_name": row.get("full_name", "").strip(),
                "phone": row.get("phone", "").strip() or None,
                "email": row.get("email", "").strip() or None,
                "role": row.get("role", "voter").strip(),
                "password": row.get("password", "").strip(),
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
# GET ALL USERS
# ============================================================
@router.get("/", response_model=List[schemas.UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    query = ListUsersQuery()
    handler = ListUsersHandler(db)
    return handler.handle(query)


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
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="ENABLE_ALL_VOTERS",
        target_type="VOTERS",
        details="Enabled all voters",
        admin_id=current_user.id,
    )
    return result
