"""
API routes for blogs.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import schemas
from ..access_control import AccessLevel, require_access_level
from ..database import get_db
from ..oauth2 import get_current_user, get_optional_current_user
from ..repository import blog as blog_repo

router = APIRouter(
    prefix="/blog",
    tags=["Blogs"]
)


@router.get("/", response_model=List[schemas.BlogResponse])
def get_all_blogs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
):
    return blog_repo.get_all_blogs(db, skip=skip, limit=limit, search=search)


@router.get("/my", response_model=List[schemas.BlogResponse])
def get_my_blogs(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
    skip: int = 0,
    limit: int = 20,
):
    return blog_repo.get_my_blogs(db, current_user.id, skip=skip, limit=limit)


@router.get("/feed/following", response_model=List[schemas.BlogResponse])
def get_following_feed(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
    skip: int = 0,
    limit: int = 20,
):
    return blog_repo.get_following_feed(db, current_user.id, skip=skip, limit=limit)


@router.get("/bookmarks", response_model=List[schemas.BlogResponse])
def get_my_bookmarks(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
):
    return blog_repo.get_bookmarked_blogs(db, current_user.id)


@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return blog_repo.get_categories(db)


@router.get("/tags", response_model=List[schemas.TagResponse])
def get_tags(db: Session = Depends(get_db)):
    return blog_repo.get_tags(db)


@router.post("/", response_model=schemas.BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog(
    request: schemas.BlogRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    return blog_repo.create_blog(request, db, current_user.id)


@router.get("/slug/{slug}", response_model=schemas.BlogResponse)
def get_blog_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.TokenData] = Depends(get_optional_current_user),
):
    return blog_repo.get_blog_by_slug(slug, db, current_user_id=current_user.id if current_user else None)


@router.post("/{blog_id}/publish", response_model=schemas.BlogResponse)
def publish_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    return blog_repo.publish_blog(blog_id, db, current_user.id, current_user.role)


@router.post("/{blog_id}/unpublish", response_model=schemas.BlogResponse)
def unpublish_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    return blog_repo.unpublish_blog(blog_id, db, current_user.id, current_user.role)


@router.post("/{blog_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    blog_id: int,
    request: schemas.CommentRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
):
    return blog_repo.add_comment(blog_id, request, db, current_user.id)


@router.get("/{blog_id}/comments", response_model=List[schemas.CommentResponse])
def get_comments(blog_id: int, db: Session = Depends(get_db)):
    return blog_repo.get_comments(blog_id, db)


@router.post("/{blog_id}/like", response_model=schemas.InteractionResponse)
def toggle_like(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
):
    return blog_repo.toggle_like(blog_id, db, current_user.id)


@router.post("/{blog_id}/bookmark", response_model=schemas.InteractionResponse)
def toggle_bookmark(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
):
    return blog_repo.toggle_bookmark(blog_id, db, current_user.id)


@router.post("/{blog_id}/share", response_model=schemas.InteractionResponse)
def share_blog(blog_id: int, db: Session = Depends(get_db)):
    return blog_repo.share_blog(blog_id, db)


@router.post("/{blog_id}/report", response_model=schemas.InteractionResponse)
def report_blog(
    blog_id: int,
    request: schemas.ReportRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.READER)),
):
    return blog_repo.report_blog(blog_id, request, db, current_user.id)


@router.get("/{blog_id}", response_model=schemas.BlogResponse)
def get_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.TokenData] = Depends(get_optional_current_user),
):
    return blog_repo.get_blog_by_id(blog_id, db, current_user_id=current_user.id if current_user else None)


@router.patch("/{blog_id}", response_model=schemas.BlogResponse)
def update_blog(
    blog_id: int,
    request: schemas.BlogUpdateRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    return blog_repo.update_blog(blog_id, request, db, current_user.id, current_user.role)


@router.put("/{blog_id}", response_model=schemas.BlogResponse)
def replace_blog(
    blog_id: int,
    request: schemas.BlogRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    update_request = schemas.BlogUpdateRequest(**request.model_dump())
    return blog_repo.update_blog(blog_id, update_request, db, current_user.id, current_user.role)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(require_access_level(AccessLevel.AUTHOR)),
):
    return blog_repo.delete_blog(blog_id, db, current_user.id, current_user.role)
