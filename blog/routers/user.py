from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas
from ..database import get_db
from ..repository import user as user_repo

router = APIRouter(
    prefix='/user',
    tags=['Users']
)

@router.post("/", response_model=schemas.show_user, status_code=status.HTTP_201_CREATED)
def create_user(request: schemas.create_user, db: Session = Depends(get_db)):
    return user_repo.create(request, db)


@router.get("/{id}", response_model=schemas.show_user)
def get_user(id: int, db: Session = Depends(get_db)):
    return user_repo.get_by_id(id, db)


@router.get("/", response_model=List[schemas.show_user])
def show_all_users(db: Session = Depends(get_db)):
    return user_repo.get_all(db)