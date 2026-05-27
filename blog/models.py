"""
SQLAlchemy database models for the application.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


def utc_now():
    """Returns the current UTC time."""
    return datetime.now(timezone.utc)


blog_tags = Table(
    "blog_tags",
    Base.metadata,
    Column("blog_id", ForeignKey("blogs.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Blog(Base):
    """Represents a blog post authored by a user."""
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String)
    is_public = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    creator = relationship("User", back_populates="blogs")
    category = relationship("Category", back_populates="blogs")
    tags = relationship("Tag", secondary=blog_tags, back_populates="blogs")
    comments = relationship("Comment", back_populates="blog", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="blog", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="blog", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="blog", cascade="all, delete-orphan")


class User(Base):
    """Represents a registered user in the system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="author", nullable=False)
    bio = Column(Text)
    avatar_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    blogs = relationship("Blog", back_populates="creator", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="reporter", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    followers = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    """Stores JWT refresh tokens for session management."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    token_hash = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="refresh_tokens")


class Category(Base):
    """Represents a category for organizing blogs."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    blogs = relationship("Blog", back_populates="category")


class Tag(Base):
    """Represents a tag for filtering blogs."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    blogs = relationship("Blog", secondary=blog_tags, back_populates="tags")


class Comment(Base):
    """Represents a user comment on a blog post."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    blog = relationship("Blog", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("Comment", cascade="all, delete-orphan")


class Like(Base):
    """Represents a user's like on a blog post."""
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("blog_id", "user_id", name="uq_blog_like_user"),)

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    blog = relationship("Blog", back_populates="likes")
    user = relationship("User", back_populates="likes")


class Bookmark(Base):
    """Represents a bookmarked blog post by a user."""
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("blog_id", "user_id", name="uq_blog_bookmark_user"),)

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    blog = relationship("Blog", back_populates="bookmarks")
    user = relationship("User", back_populates="bookmarks")


class Report(Base):
    """Represents a report filed against a blog post."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reason = Column(String, nullable=False)
    details = Column(Text)
    status = Column(String, default="open")
    blog_id = Column(Integer, ForeignKey("blogs.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    blog = relationship("Blog", back_populates="reports")
    reporter = relationship("User", back_populates="reports")


class Follow(Base):
    """Represents a follow relationship between two users."""
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),)

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")
