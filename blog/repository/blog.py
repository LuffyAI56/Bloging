from fastapi import HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas


def get_all(db: Session, skip: int = 0, limit: int = 5):
    return db.query(models.Blog).offset(skip).limit(limit).all()


def create(request: schemas.Blog, db: Session, user_id: int):
    new_blog = models.Blog(**request.model_dump(), user_id=user_id)
    try:
        db.add(new_blog)
        db.commit()
        db.refresh(new_blog)
    except:
        db.rollback()
        raise
    return new_blog


def get_by_id(id: int, db: Session):
    blog = db.get(models.Blog, id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


def delete(id: int, db: Session, user_id: int):
    blog = db.get(models.Blog, id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(blog)
    db.commit()
    return {"message": "deleted"}


def update(id: int, request: schemas.Blog, db: Session, user_id: int):
    blog = db.get(models.Blog, id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(blog, key, value)
    db.commit()
    db.refresh(blog)
    return blog