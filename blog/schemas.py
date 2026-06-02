"""
Pydantic schemas for data validation and serialization.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .utils import sanitize_text


VALID_ROLES = {"reader", "author", "admin"}


def normalize_email_value(value: str):
    email = value.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("Enter a valid email address")
    return email


def validate_text_field(value: str, field_name: str, max_length: int):
    if value is None:
        return None
    return sanitize_text(value, max_length=max_length)


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


class EmailOTPRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return normalize_email_value(value)


class VerifyOTPRequest(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return normalize_email_value(value)


class CreateUserRequest(BaseModel):
    """Request model for user registration."""
    name: str
    email: str
    password: str
    otp: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        return validate_text_field(value, "name", max_length=100)

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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]):
        return validate_text_field(value, "name", max_length=100)

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, value: Optional[str]):
        return validate_text_field(value, "bio", max_length=500)

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if len(value) > 2048:
            raise ValueError("Avatar URL must be 2048 characters or fewer")
        return sanitize_text(value, max_length=2048)


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

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str):
        return validate_text_field(value, "title", max_length=250)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        return validate_text_field(value, "content", max_length=20000)

    @field_validator("cover_image_url")
    @classmethod
    def validate_cover_image_url(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if len(value) > 1024:
            raise ValueError("Cover image URL must be 1024 characters or fewer")
        return sanitize_text(value, max_length=1024)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: Optional[str]):
        return validate_text_field(value, "category", max_length=100)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("tags must be a list")
        return [sanitize_text(tag, max_length=50) for tag in value if tag and tag.strip()]


class BlogUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_published: Optional[bool] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]):
        return validate_text_field(value, "title", max_length=250)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: Optional[str]):
        return validate_text_field(value, "content", max_length=20000)

    @field_validator("cover_image_url")
    @classmethod
    def validate_cover_image_url(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if len(value) > 1024:
            raise ValueError("Cover image URL must be 1024 characters or fewer")
        return sanitize_text(value, max_length=1024)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: Optional[str]):
        return validate_text_field(value, "category", max_length=100)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value):
        if value is None:
            return value
        if not isinstance(value, list):
            raise TypeError("tags must be a list")
        return [sanitize_text(tag, max_length=50) for tag in value if tag and tag.strip()]


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
    likes_count: int = 0
    bookmarks_count: int = 0
    comments_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: PublicUserResponse
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = Field(default_factory=list)


class SuggestedAuthorResponse(BaseModel):
    user: PublicUserResponse
    followers_count: int = 0
    posts_count: int = 0
    is_following: bool = False


class TrendingTagResponse(TagResponse):
    post_count: int = 0


class CommentRequest(BaseModel):
    """Request model for adding a comment."""
    content: str
    parent_id: Optional[int] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        return validate_text_field(value, "comment content", max_length=2000)


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

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str):
        return validate_text_field(value, "report reason", max_length=150)

    @field_validator("details")
    @classmethod
    def validate_details(cls, value: Optional[str]):
        return validate_text_field(value, "report details", max_length=2000)


class InteractionResponse(BaseModel):
    """Response model for generic interactions (like, share, etc.)."""
    message: str
    active: bool = True


class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[int] = None
    role: Optional[str] = None
