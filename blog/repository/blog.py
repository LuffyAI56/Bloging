"""
Data access layer for blogs.
"""

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils import unique_slug

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

def get_or_create_category(db: Session, name: str | None):

    """Handles get or create category logic."""

    if not name:
        return None

    normalized_name = name.strip()
    category = db.query(models.Category).filter(models.Category.name == normalized_name).first()
    if category:
        return category

    slug = unique_slug(db, models.Category, normalized_name)
    category = models.Category(name=normalized_name, slug=slug)
    db.add(category)
    db.flush()
    return category


def get_or_create_tags(db: Session, names: list[str]):
    """Handles get or create tags logic."""
    tags = []
    for name in names:
        normalized_name = name.strip()
        if not normalized_name:
            continue

        tag = db.query(models.Tag).filter(models.Tag.name == normalized_name).first()
        if not tag:
            tag = models.Tag(name=normalized_name, slug=unique_slug(db, models.Tag, normalized_name))
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def base_visible_query(db: Session):
    """Handles base visible query logic."""
    return db.query(models.Blog).filter(
        models.Blog.is_public == True,
        models.Blog.is_published == True,
    )




def get_all_blogs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
):
    """Handles get all blogs logic."""

    query = (
        base_visible_query(db).options(
            selectinload(models.Blog.tags),
            selectinload(models.Blog.category),
            selectinload(models.Blog.creator),
        )
    )
    if search:
        search = search.strip()

        if search:
            pattern = f"%{search}%"

            query = query.filter(
                or_(
                    models.Blog.title.ilike(pattern),
                    models.Blog.content.ilike(pattern),
                )
            )
    return (
        query.order_by(models.Blog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_my_blogs(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    """Handles get my blogs logic."""
    return db.query(models.Blog).filter(
        models.Blog.user_id == user_id
    ).order_by(models.Blog.created_at.desc()).offset(skip).limit(limit).all()


def create_blog(request: schemas.BlogRequest, db: Session, user_id: int):
    """Handles create blog logic."""
    category = get_or_create_category(db, request.category)
    new_blog = models.Blog(
        title=request.title,
        slug=unique_slug(db, models.Blog, request.title),
        content=request.content,
        cover_image_url=request.cover_image_url,
        is_public=request.is_public,
        is_published=request.is_published,
        category=category,
        user_id=user_id,
    )
    db.add(new_blog)
    new_blog.tags = get_or_create_tags(db, request.tags)

    try:
        db.commit()
        db.refresh(new_blog)
    except Exception:
        db.rollback()
        raise
    return new_blog


def get_blog_by_id(blog_id: int, db: Session, current_user_id: int | None = None, increment_view: bool = True):
    """Handles get blog by id logic."""
    blog = db.get(models.Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    can_view_private = current_user_id is not None and blog.user_id == current_user_id
    if (not blog.is_public or not blog.is_published) and not can_view_private:
        raise HTTPException(status_code=404, detail="Blog not found")

    if increment_view:
        blog.view_count = (blog.view_count or 0) + 1
        db.commit()
        db.refresh(blog)

    return blog


def get_blog_by_slug(slug: str, db: Session, current_user_id: int | None = None):
    """Handles get blog by slug logic."""
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return get_blog_by_id(blog.id, db, current_user_id=current_user_id)


def assert_blog_owner_or_admin(blog: models.Blog, user_id: int, role: str | None):
    """Handles assert blog owner or admin logic."""
    if blog.user_id != user_id and role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")


def delete_blog(blog_id: int, db: Session, user_id: int, role: str | None = None):
    """Handles delete blog logic."""
    blog = db.get(models.Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    assert_blog_owner_or_admin(blog, user_id, role)

    db.delete(blog)
    db.commit()
    return None


def update_blog(blog_id: int, request: schemas.BlogUpdateRequest, db: Session, user_id: int, role: str | None = None):
    """Handles update blog logic."""
    blog = db.get(models.Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    assert_blog_owner_or_admin(blog, user_id, role)
    update_data = request.model_dump(exclude_unset=True)

    if "title" in update_data and update_data["title"] != blog.title:
        blog.slug = unique_slug(db, models.Blog, update_data["title"])

    if "category" in update_data:
        blog.category = get_or_create_category(db, update_data.pop("category"))

    if "tags" in update_data:
        blog.tags = get_or_create_tags(db, update_data.pop("tags") or [])

    for key, value in update_data.items():
        setattr(blog, key, value)

    db.commit()
    db.refresh(blog)
    return blog


def publish_blog(blog_id: int, db: Session, user_id: int, role: str | None = None):
    """Handles publish blog logic."""
    return update_blog(blog_id, schemas.BlogUpdateRequest(is_published=True), db, user_id, role)


def unpublish_blog(blog_id: int, db: Session, user_id: int, role: str | None = None):
    """Handles unpublish blog logic."""
    return update_blog(blog_id, schemas.BlogUpdateRequest(is_published=False), db, user_id, role)


def add_comment(blog_id: int, request: schemas.CommentRequest, db: Session, user_id: int):
    """Handles add comment logic."""
    get_blog_by_id(blog_id, db, current_user_id=user_id, increment_view=False)

    if request.parent_id:
        parent = db.get(models.Comment, request.parent_id)
        if not parent or parent.blog_id != blog_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    comment = models.Comment(
        blog_id=blog_id,
        user_id=user_id,
        parent_id=request.parent_id,
        content=request.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(blog_id: int, db: Session):
    """Handles get comments logic."""
    return db.query(models.Comment).filter(models.Comment.blog_id == blog_id).order_by(models.Comment.created_at.asc()).all()


def toggle_like(blog_id: int, db: Session, user_id: int):
    """Handles toggle like logic."""
    get_blog_by_id(blog_id, db, current_user_id=user_id, increment_view=False)
    like = db.query(models.Like).filter(models.Like.blog_id == blog_id, models.Like.user_id == user_id).first()

    if like:
        db.delete(like)
        db.commit()
        return schemas.InteractionResponse(message="Like removed", active=False)

    db.add(models.Like(blog_id=blog_id, user_id=user_id))
    db.commit()
    return schemas.InteractionResponse(message="Post liked", active=True)


def toggle_bookmark(blog_id: int, db: Session, user_id: int):
    """Handles toggle bookmark logic."""
    get_blog_by_id(blog_id, db, current_user_id=user_id, increment_view=False)
    bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.blog_id == blog_id,
        models.Bookmark.user_id == user_id,
    ).first()

    if bookmark:
        db.delete(bookmark)
        db.commit()
        return schemas.InteractionResponse(message="Bookmark removed", active=False)

    db.add(models.Bookmark(blog_id=blog_id, user_id=user_id))
    db.commit()
    return schemas.InteractionResponse(message="Post bookmarked", active=True)


def get_bookmarked_blogs(db: Session, user_id: int):
    """Handles get bookmarked blogs logic."""
    return db.query(models.Blog).join(models.Bookmark).filter(models.Bookmark.user_id == user_id).all()


def share_blog(blog_id: int, db: Session):
    """Handles share blog logic."""
    blog = get_blog_by_id(blog_id, db, increment_view=False)
    blog.share_count = (blog.share_count or 0) + 1
    db.commit()
    return schemas.InteractionResponse(message="Share counted", active=True)


def report_blog(blog_id: int, request: schemas.ReportRequest, db: Session, user_id: int):
    """Handles report blog logic."""
    get_blog_by_id(blog_id, db, current_user_id=user_id, increment_view=False)
    report = models.Report(
        blog_id=blog_id,
        reporter_id=user_id,
        reason=request.reason,
        details=request.details,
    )
    db.add(report)
    db.commit()
    return schemas.InteractionResponse(message="Report submitted", active=True)

from sqlalchemy import exists
from sqlalchemy.orm import selectinload

def get_following_feed(
    db: Session,
    user_id: int,
    limit: int = 20,
    cursor=None,
):
    """Handles following feed logic."""

    query = (
        base_visible_query(db)
        .options(
            selectinload(models.Blog.creator),
            selectinload(models.Blog.tags),
            selectinload(models.Blog.category),
        )
        .filter(
            exists().where(
                (models.Follow.following_id == models.Blog.user_id)
                & (models.Follow.follower_id == user_id)
            )
        )
    )

    if cursor:
        query = query.filter(models.Blog.created_at < cursor)

    return (
        query.order_by(models.Blog.created_at.desc())
        .limit(limit)
        .all()
    )

def get_categories(db: Session):
    """Handles get categories logic."""
    return db.query(models.Category).order_by(models.Category.name.asc()).all()


def get_tags(db: Session):
    """Handles get tags logic."""
    return db.query(models.Tag).order_by(models.Tag.name.asc()).all()