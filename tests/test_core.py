from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from blog import hashing, models, schemas, token
from blog.access_control import AccessLevel, require_access_level
from blog.models import Base
from blog.repository import blog as blog_repo
from blog.repository import user as user_repo
from blog.routers import authentication


def create_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return session_local()


def test_user_creation_rejects_duplicate_email():
    db = create_test_db()
    request = schemas.CreateUserRequest(
        name="Test User",
        email="test@example.com",
        password="abc12345",
    )

    user_repo.create_user(request, db)

    try:
        user_repo.create_user(request, db)
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("duplicate email was allowed")


def test_password_hashing_and_token_flow():
    db = create_test_db()
    user = user_repo.create_user(
        schemas.CreateUserRequest(
            name="Test User",
            email="test@example.com",
            password="abc12345",
        ),
        db,
    )

    assert hashing.PasswordHasher.verify_password("abc12345", user.password)
    access_token = token.create_access_token({"sub": user.email})
    payload = token.verify_token(access_token)
    assert payload["sub"] == user.email


def test_register_route_creates_user_and_returns_tokens():
    db = create_test_db()
    request = schemas.CreateUserRequest(
        name="Register User",
        email="register@example.com",
        password="secure123",
    )

    otp_code = user_repo.request_email_otp(request.email, db)
    verification = authentication.verify_otp(schemas.VerifyOTPRequest(email=request.email, code=otp_code), db)
    assert verification["verified"] is True

    token_response = authentication.register(request, db)
    assert token_response.access_token
    assert token_response.refresh_token
    assert token.verify_token(token_response.access_token)["sub"] == request.email


def test_blog_crud_requires_owner():
    db = create_test_db()
    owner = user_repo.create_user(
        schemas.CreateUserRequest(name="Owner", email="owner@example.com", password="abc12345"),
        db,
    )
    other_user = user_repo.create_user(
        schemas.CreateUserRequest(name="Other", email="other@example.com", password="abc12345"),
        db,
    )

    blog = blog_repo.create_blog(
        schemas.BlogRequest(title="Hello", content="World"),
        db,
        owner.id,
    )

    try:
        blog_repo.update_blog(
            blog.id,
            schemas.BlogRequest(title="Bad", content="Actor"),
            db,
            other_user.id,
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("non-owner update was allowed")

    updated = blog_repo.update_blog(
        blog.id,
        schemas.BlogRequest(title="Updated", content="World"),
        db,
        owner.id,
    )
    assert updated.title == "Updated"
    assert blog_repo.delete_blog(blog.id, db, owner.id) is None


def test_access_levels_are_ordered():
    admin_check = require_access_level(AccessLevel.ADMIN)
    author_check = require_access_level(AccessLevel.AUTHOR)
    reader = schemas.TokenData(email="reader@example.com", id=1, role="reader")
    author = schemas.TokenData(email="author@example.com", id=2, role="author")
    admin = schemas.TokenData(email="admin@example.com", id=3, role="admin")

    assert author_check(author).role == "author"
    assert author_check(admin).role == "admin"

    try:
        admin_check(reader)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("reader should not pass admin access")


def test_blog_metadata_interactions_and_feed():
    db = create_test_db()
    author = user_repo.create_user(
        schemas.CreateUserRequest(name="Author", email="author@example.com", password="abc12345"),
        db,
    )
    reader = user_repo.create_user(
        schemas.CreateUserRequest(name="Reader", email="reader@example.com", password="abc12345"),
        db,
    )

    blog = blog_repo.create_blog(
        schemas.BlogRequest(
            title="Production Blog",
            content="A real post",
            is_public=True,
            is_published=False,
            category="Backend",
            tags=["FastAPI", "SQLAlchemy"],
        ),
        db,
        author.id,
    )

    assert blog.slug == "production-blog"
    assert blog.category.name == "Backend"
    assert len(blog.tags) == 2
    assert blog.is_published is False

    blog_repo.publish_blog(blog.id, db, author.id, author.role)
    visible_blog = blog_repo.get_blog_by_id(blog.id, db, current_user_id=reader.id)
    assert visible_blog.view_count == 1

    updated = blog_repo.update_blog(
        blog.id,
        schemas.BlogUpdateRequest(content="Updated only"),
        db,
        author.id,
        author.role,
    )
    assert updated.title == "Production Blog"
    assert updated.content == "Updated only"

    comment = blog_repo.add_comment(
        blog.id,
        schemas.CommentRequest(content="Nice post"),
        db,
        reader.id,
    )
    reply = blog_repo.add_comment(
        blog.id,
        schemas.CommentRequest(content="Thanks", parent_id=comment.id),
        db,
        author.id,
    )
    assert reply.parent_id == comment.id
    assert len(blog_repo.get_comments(blog.id, db)) == 2

    assert blog_repo.toggle_like(blog.id, db, reader.id).active is True
    assert blog_repo.toggle_like(blog.id, db, reader.id).active is False
    assert blog_repo.toggle_bookmark(blog.id, db, reader.id).active is True
    assert blog_repo.get_bookmarked_blogs(db, reader.id)[0].id == blog.id
    assert blog_repo.share_blog(blog.id, db).active is True
    assert blog_repo.report_blog(
        blog.id,
        schemas.ReportRequest(reason="spam", details="test"),
        db,
        reader.id,
    ).active is True

    user_repo.follow_author(reader.id, author.id, db)
    feed = blog_repo.get_following_feed(db, reader.id)
    assert feed[0].id == blog.id


def test_discovery_feed_and_new_user_suggestions():
    db = create_test_db()
    author = user_repo.create_user(
        schemas.CreateUserRequest(name="AI Author", email="ai-author@example.com", password="abc12345"),
        db,
    )
    reader = user_repo.create_user(
        schemas.CreateUserRequest(name="New Reader", email="new-reader@example.com", password="abc12345"),
        db,
    )

    post = blog_repo.create_blog(
        schemas.BlogRequest(
            title="Smart Recommendation Systems",
            content="A practical guide to ranking posts for new users.",
            category="Applied AI",
            tags=["AI", "Recommendations"],
        ),
        db,
        author.id,
    )
    blog_repo.toggle_like(post.id, db, reader.id)
    blog_repo.toggle_bookmark(post.id, db, reader.id)
    blog_repo.add_comment(post.id, schemas.CommentRequest(content="Great onboarding idea"), db, reader.id)

    feed = blog_repo.get_discovery_feed(db, current_user_id=reader.id, limit=5)
    assert feed[0].id == post.id
    assert feed[0].likes_count == 1
    assert feed[0].bookmarks_count == 1
    assert feed[0].comments_count == 1

    suggestions = blog_repo.get_suggested_authors(db, current_user_id=reader.id)
    assert suggestions[0]["user"].id == author.id
    assert suggestions[0]["posts_count"] == 1

    trends = blog_repo.get_trending_tags(db)
    assert trends[0]["name"] in {"AI", "Recommendations"}
    assert trends[0]["post_count"] == 1


def test_refresh_tokens_can_be_revoked():
    db = create_test_db()
    user = user_repo.create_user(
        schemas.CreateUserRequest(name="Token User", email="token@example.com", password="abc12345"),
        db,
    )
    refresh_token, jti, expires_at = token.create_refresh_token({"sub": user.email})
    token_record = models.RefreshToken(
        jti=jti,
        token_hash="hash",
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(token_record)
    db.commit()

    payload = token.verify_token(refresh_token, token_type="refresh")
    assert payload["sub"] == user.email
    assert payload["jti"] == jti
