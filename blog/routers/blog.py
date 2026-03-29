from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..repository import blog as blog_repo
from ..oauth2 import get_current_user

router = APIRouter(
    prefix='/blog',
    tags=['Blogs']
)

@router.get('/', response_model=List[schemas.show_blog])
def all(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
    skip: int = 0, 
    limit: int = 5
):
    return blog_repo.get_all(db,skip = skip , limit = limit)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_blog(
    request: schemas.Blog,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user)
):
    return blog_repo.create(request, db)

@router.get("/{id}", response_model=schemas.show_blog)
def get_blog(
    id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user)
):
    return blog_repo.get_by_id(id, db)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user)
):
    return blog_repo.delete(id, db)

@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_blog(
    id: int,
    request: schemas.Blog,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user)
    
):
    return blog_repo.update(id, request, db)