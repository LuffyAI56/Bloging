"""
Pydantic schemas for data validation and serialization.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_ROLES = {"reader", "author", "admin"}


def normalize_email_value(value: str):
    email = value.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("Enter a valid email address")
    return email


def validate_password_value(value: str):
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if value.isalpha() or value.isdigit():
        raise ValueError("Password must contain both letters and numbers")
    return value


class TokenResponse(BaseModel):
    """Response model for access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    """Request model for user registration."""
    name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return normalize_email_value(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        return validate_password_value(value)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str):
        return validate_password_value(value)


class SetUserRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str):
        role = value.strip().lower()
        if role not in VALID_ROLES:
            raise ValueError("Role must be reader, author, or admin")
        return role


class PublicUserResponse(BaseModel):
    """Response model exposing public user details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None


class AuthorProfileResponse(PublicUserResponse):
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0


class CategoryRequest(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class BlogRequest(BaseModel):
    """Request model for creating a new blog post."""
    title: str
    content: str
    cover_image_url: Optional[str] = None
    is_public: bool = True
    is_published: bool = True
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class BlogUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_published: Optional[bool] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class BlogResponse(BaseModel):
    """Response model for a blog post."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: Optional[str] = None
    content: str
    cover_image_url: Optional[str] = None
    is_public: bool
    is_published: bool
    view_count: int
    share_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: PublicUserResponse
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = Field(default_factory=list)


class CommentRequest(BaseModel):
    """Request model for adding a comment."""
    content: str
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    blog_id: int
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    user: PublicUserResponse


class ReportRequest(BaseModel):
    reason: str
    details: Optional[str] = None


class InteractionResponse(BaseModel):
    """Response model for generic interactions (like, share, etc.)."""
    message: str
    active: bool = True


class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[int] = None
    role: Optional[str] = None
