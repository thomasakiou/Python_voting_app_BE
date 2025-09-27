from fastapi import APIRouter, Depends, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core import database, oauth2
from ..schemas import office as schemas
from ..core.database import get_db
from ..application.commands.office.create_office import CreateOfficeCommand, CreateOfficeHandler
from ..application.commands.office.delete_office import DeleteOfficeCommand, DeleteOfficeHandler
from ..application.commands.office.update_office import UpdateOfficeCommand, UpdateOfficeHandler
from ..application.queries.office.get_all_offices import ListOfficesQuery, ListOfficesHandler
from ..application.queries.office.get_office_by_code import GetOfficeByCodeQuery, GetOfficeByCodeHandler

import io, csv


router = APIRouter(prefix="/offices", tags=["Offices"])

# ==========================
# CREATE OFFICE
# ==========================
@router.post("/", response_model=schemas.OfficeResponse)
def create_office(office: schemas.OfficeCreate, db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.role_required(["super-admin"]))):


    command = CreateOfficeCommand(office_code=office.office_code, 
                                description=office.description,
                                )
    handler = CreateOfficeHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL OFFICES
# ==========================
@router.get("/", response_model=list[schemas.OfficeResponse])
def get_all_offices(db: Session = Depends(get_db),
                  current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))):
    query = ListOfficesQuery()
    handler = ListOfficesHandler(db)
    return handler.handle(query)



# ======================================
# GET OFFICE BY CANDIDATE CODE
# ======================================
@router.get("/{candidate_code}", response_model=schemas.OfficeResponse)
def get_candidate_by_code(code: str, db: Session = Depends(get_db), 
                          current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))):
    query = GetOfficeByCodeQuery(office_code=code)
    handler = GetOfficeByCodeHandler(db)
    return handler.handle(query)


# ==========================
# DELETE OFFICE BY ID
# ==========================
@router.delete("/{id}")
def delete_candidate(id: int, db: Session = Depends(get_db), 
                     current_user=Depends(oauth2.role_required(["super-admin"]))):
    command = DeleteOfficeCommand(office_id=id)
    handler = DeleteOfficeHandler(db)
    return handler.handle(command)



# ==========================
# UPDATE OFFICE BY ID
# ==========================
@router.put("/{id}", response_model=schemas.OfficeResponse)
def update_office(id: int, office: schemas.OfficeUpdate, db: Session = Depends(get_db), 
                current_user=Depends(oauth2.role_required(["super-admin"]))):
    command = UpdateOfficeCommand(office_id=id,
                                  office_code=office.office_code, 
                                  description=office.description 
                                    )
    handler = UpdateOfficeHandler(db)
    return handler.handle(command)