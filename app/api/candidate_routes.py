from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core import database, oauth2
from ..schemas import candidate as schemas
from ..core.config import settings
from ..core.database import get_db
from fastapi import APIRouter, Depends
from typing import List
from ..application.commands.candidate.create_candidate import CreateCandidateCommand, CreateCandidateHandler
from ..application.queries.candidate.get_all_candidates import ListCandidatesHandler, ListCandidatesQuery
from ..application.queries.candidate.get_candidate_by_code import GetCandidateByCodeQuery, GetCandidateByCodeHandler
from ..application.queries.candidate.get_candidate_by_office_code import GetCandidateByOfficeCodeQuery, GetCandidateByOfficeCodeHandler
from ..application.commands.candidate.delete_candidate import DeleteCandidateCommand, DeleteCandidateHandler
from ..application.commands.candidate.update_candidate import UpdateCandidateCommand, UpdateCandidateHandler



router = APIRouter(prefix=f"{settings.api_prefix}/candidates", tags=["Candidates"])

# ==========================
# CREATE CANDIDATES
# ==========================
@router.post("/", response_model=schemas.CandidateResponse)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.role_required(["super-admin"]))):


    command = CreateCandidateCommand(
                                    candidate_code=candidate.candidate_code, 
                                    name=candidate.name, 
                                    office_code=candidate.office_code

                                )
    handler = CreateCandidateHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL CANDIDATES
# ==========================
@router.get("/", response_model=list[schemas.CandidateResponse])
def get_all_candidates(db: Session = Depends(get_db),
                  current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))):
    query = ListCandidatesQuery()
    handler = ListCandidatesHandler(db)
    return handler.handle(query)



# ======================================
# GET CANDIDATE BY OFFICE CODE
# ======================================
@router.get("/{office_code}/candidates", response_model=List[schemas.CandidateResponse])
def get_candidates_by_office_code(office_code: str,
                                   db: Session = Depends(get_db), 
                                   current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))):
    
    query = GetCandidateByOfficeCodeQuery(office_code=office_code)
    handler = GetCandidateByOfficeCodeHandler(db)
    return handler.handle(query)




# ==========================
# GET CANDIDATES BY CODE
# ==========================
@router.get("/{candidate_code}", response_model=schemas.CandidateResponse)
def get_candidate_by_code(code: str, db: Session = Depends(get_db), 
                          current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))):
    query = GetCandidateByCodeQuery(candidate_code=code)
    handler = GetCandidateByCodeHandler(db)
    return handler.handle(query)



# ==========================
# DELETE CANDIDATE BY ID
# ==========================
@router.delete("/{id}")
def delete_candidate(id: int, db: Session = Depends(get_db), 
                     current_user=Depends(oauth2.role_required(["super-admin"]))):
    command = DeleteCandidateCommand(candidate_id=id)
    handler = DeleteCandidateHandler(db)
    return handler.handle(command)




# ==========================
# UPDATE CANDIDATE BY ID
# ==========================
@router.put("/{id}", response_model=schemas.CandidateResponse)
def update_candidate(id: int, candidate: schemas.CandidateCreate, db: Session = Depends(get_db), 
                current_user=Depends(oauth2.role_required(["super-admin"]))):
    command = UpdateCandidateCommand(candidate_id=id,
                                     candidate_code=candidate.candidate_code, 
                                     name=candidate.name, 
                                     office_code=candidate.office_code)
    handler = UpdateCandidateHandler(db)
    return handler.handle(command)
