from fastapi import APIRouter, Depends, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core import database, oauth2
from ..schemas import user as schemas
from ..core.database import get_db
from ..application.commands.user.create_user import CreateUserCommand, CreateUserHandler, ImportVotersCommand, ImportVotersHandler
from ..application.commands.user.delete_user import DeleteUserCommand, DeleteUserHandler
from ..application.queries.user.get_all_users import ListUsersQuery, ListUsersHandler
from ..application.queries.user.get_user_by_username import GetUserByUsernameQuery, GetUserByUsernameHandler

import io, csv


router = APIRouter(prefix="/users", tags=["Users"])

# ==========================
# CREATE USER (ADMIN)
# ==========================
@router.post("/admin", response_model=schemas.UserOut)
def create_admin_user(user: schemas.UserCreate, db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.role_required(["super-admin"]))):

    # hashed_password = utils.hash(user.password)
    # user.password = hashed_password

    command = CreateUserCommand(username=user.username, 
                                password=user.password,
                                full_name=user.full_name,
                                phone=user.phone,
                                role= "admin",
                                must_change_password=False
                                )
    handler = CreateUserHandler(db)
    return handler.handle(command)



# ==========================
# CREATE USER (VOTER)
# ==========================
@router.post("/voter", response_model=schemas.UserOut)
def create_voter_user(user: schemas.UserCreate, db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):

    # hashed_password = utils.hash(user.password)
    # user.password = hashed_password

    command = CreateUserCommand(username=user.username, 
                                password=user.password,
                                full_name=user.full_name,
                                phone=user.phone,
                                role= "voter",
                                must_change_password=True
                                )
    handler = CreateUserHandler(db)
    return handler.handle(command)



# =============================================
# UPLOAD USER-CSV (VOTER)
# =============================================
@router.post("/upload-csv")
def upload_voters_csv(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"]))
):
    # Ensure file is CSV
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed."
        )

    try:
        contents = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}"
        )

    voters = []
    try:
        for row in reader:
            voters.append({
                "username": row["username"],
                "full_name": row.get("full_name", ""),
                "phone": row.get("phone"),
                "role": row.get("role"),
                "password": row.get("password")
            })
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required column in CSV: {str(e)}"
        )

    command = ImportVotersCommand(voters=voters)
    handler = ImportVotersHandler(db)
    created = handler.handle(command)

    return {
        "created": len(created),
        "users": [u.username for u in created]
    }



# ==========================
# GET ALL USER
# ==========================
@router.get("/", response_model=list[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db),
                  current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
    query = ListUsersQuery()
    handler = ListUsersHandler(db)
    return handler.handle(query)


# ==========================
# GET USER BY USERNAME
# ==========================
@router.get("/{username}", response_model=schemas.UserOut)
def get_user(name: str, db: Session = Depends(get_db), current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
    query = GetUserByUsernameQuery(username=name)
    handler = GetUserByUsernameHandler(db)
    return handler.handle(query)



# ==========================
# DELETE USER BY ID
# ==========================
@router.delete("/{id}")
def delete_user(id: int, db: Session = Depends(get_db), current_user=Depends(oauth2.role_required(["super-admin"]))):
    command = DeleteUserCommand(user_id=id)
    handler = DeleteUserHandler(db)
    return handler.handle(command)



# ==========================
# UPDATE USER BY ID
# ==========================
# @router.put("/{id}", response_model=schemas.UserOut)
# def update_user(id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
#     command = update_user.UpdateUserCommand(user_id=id, full_name=user.full_name, email=user.email)
#     handler = update_user.UpdateUserHandler(db)
#     return handler.handle(command)





