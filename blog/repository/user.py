"""
Data access layer for users.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import hashing, models, schemas


def create_user(request: schemas.CreateUserRequest, db: Session):
    """Handles create user logic."""
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    new_user = models.User(
        name=request.name,
        email=request.email,
        password=hashing.PasswordHasher.hash_password(request.password),
        role="author"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(user_id: int, db: Session):
    """Handles get user by id logic."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return user


def get_all_users(db: Session):
    """Handles get all users logic."""
    return db.query(models.User).filter(models.User.is_active == True).all()


def update_user_profile(user_id: int, request: schemas.UpdateUserRequest, db: Session):
    """Handles update user profile logic."""
    user = get_user_by_id(user_id, db)
    update_data = request.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def change_password(user_id: int, request: schemas.ChangePasswordRequest, db: Session):
    """Handles change password logic."""
    user = get_user_by_id(user_id, db)

    if not hashing.PasswordHasher.verify_password(request.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    user.password = hashing.PasswordHasher.hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed"}


def delete_account(user_id: int, db: Session):
    """Handles delete account logic."""
    user = get_user_by_id(user_id, db)
    user.is_active = False
    db.commit()
    return None


def set_user_role(user_id: int, request: schemas.SetUserRoleRequest, db: Session):
    """Handles set user role logic."""
    user = get_user_by_id(user_id, db)
    user.role = request.role
    db.commit()
    db.refresh(user)
    return user


def get_author_profile(user_id: int, db: Session):
    """Handles get author profile logic."""
    user = get_user_by_id(user_id, db)
    return {
        **schemas.PublicUserResponse.model_validate(user).model_dump(),
        "followers_count": db.query(models.Follow).filter(models.Follow.following_id == user_id).count(),
        "following_count": db.query(models.Follow).filter(models.Follow.follower_id == user_id).count(),
        "posts_count": db.query(models.Blog).filter(
            models.Blog.user_id == user_id,
            models.Blog.is_published == True,
            models.Blog.is_public == True,
        ).count(),
    }


def follow_author(current_user_id: int, author_id: int, db: Session):
    """Handles follow author logic."""
    if current_user_id == author_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    get_user_by_id(author_id, db)
    existing_follow = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user_id,
        models.Follow.following_id == author_id,
    ).first()

    if existing_follow:
        return schemas.InteractionResponse(message="Already following", active=True)

    db.add(models.Follow(follower_id=current_user_id, following_id=author_id))
    db.commit()
    return schemas.InteractionResponse(message="Following author", active=True)


def unfollow_author(current_user_id: int, author_id: int, db: Session):
    """Handles unfollow author logic."""
    follow = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user_id,
        models.Follow.following_id == author_id,
    ).first()

    if follow:
        db.delete(follow)
        db.commit()

    return schemas.InteractionResponse(message="Unfollowed author", active=False)
