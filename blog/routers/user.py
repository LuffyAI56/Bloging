"""
API routes for users.
"""
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import schemas
from ..access_control import AccessLevel, require_access_level
from ..database import get_db
from ..oauth2 import get_current_user
from ..repository import user as user_repo

router = APIRouter(
    prefix="/user",
    tags=["Users"]
)


@router.post("/", response_model=schemas.PublicUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: schemas.CreateUserRequest, db: Session = Depends(get_db)):
    return user_repo.create_user(request, db)


@router.get("/me", response_model=schemas.PublicUserResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.get_user_by_id(current_user.id, db)


@router.put("/me", response_model=schemas.PublicUserResponse)
def update_me(
    request: schemas.UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.update_user_profile(current_user.id, request, db)


@router.post("/me/change-password")
def change_my_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.change_password(current_user.id, request, db)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.delete_account(current_user.id, db)


@router.get("/{user_id}/profile", response_model=schemas.AuthorProfileResponse)
def get_author_profile(user_id: int, db: Session = Depends(get_db)):
    return user_repo.get_author_profile(user_id, db)


@router.post("/{user_id}/follow", response_model=schemas.InteractionResponse)
def follow_author(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.follow_author(current_user.id, user_id, db)


@router.delete("/{user_id}/follow", response_model=schemas.InteractionResponse)
def unfollow_author(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(get_current_user),
):
    return user_repo.unfollow_author(current_user.id, user_id, db)


@router.put("/{user_id}/role", response_model=schemas.PublicUserResponse)
def set_user_role(
    user_id: int,
    request: schemas.SetUserRoleRequest,
    db: Session = Depends(get_db),
    _: schemas.TokenData = Depends(require_access_level(AccessLevel.ADMIN)),
):
    return user_repo.set_user_role(user_id, request, db)


@router.get("/{user_id}", response_model=schemas.PublicUserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_repo.get_user_by_id(user_id, db)


@router.get("/", response_model=List[schemas.PublicUserResponse])
def show_all_users(
    db: Session = Depends(get_db),
    _: schemas.TokenData = Depends(require_access_level(AccessLevel.ADMIN))
):
    return user_repo.get_all_users(db)
