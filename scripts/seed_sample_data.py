"""
Seed the local Blog API database with realistic sample data.

Default output:
- 200 generated users
- 2,000 generated blog posts
- categories, tags, follows, likes, bookmarks, comments, and reports

The script is additive and safe to rerun. It creates missing seed rows up to
the requested target counts without deleting existing application data.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from blog import migrations, models
from blog.database import SessionLocal, engine
from blog.hashing import PasswordHasher
from blog.utils import slugify


SEED_READER_EMAIL = "seed_reader@example.com"
SEED_USER_EMAIL_TEMPLATE = "seed_author_{number:04d}@example.com"
SEED_POST_SLUG_PREFIX = "seed-post-"

CATEGORIES = [
    "Backend Development",
    "Frontend Engineering",
    "Applied AI",
    "Data Engineering",
    "Cloud Infrastructure",
    "Cybersecurity",
    "DevOps",
    "Product Thinking",
    "Career Growth",
    "Database Design",
    "System Design",
    "Machine Learning",
]

TAGS = [
    "fastapi",
    "python",
    "sqlalchemy",
    "jwt",
    "react",
    "typescript",
    "postgres",
    "sqlite",
    "docker",
    "testing",
    "redis",
    "apis",
    "security",
    "deployment",
    "ai",
    "llm",
    "embeddings",
    "recommendations",
    "analytics",
    "architecture",
    "performance",
    "clean-code",
    "auth",
    "ux",
]

FIRST_NAMES = [
    "Aarav",
    "Ananya",
    "Arjun",
    "Diya",
    "Ishaan",
    "Kavya",
    "Meera",
    "Neha",
    "Rohan",
    "Saanvi",
    "Vihaan",
    "Zara",
    "Aditi",
    "Dev",
    "Nisha",
    "Rahul",
    "Priya",
    "Kabir",
    "Maya",
    "Reyansh",
]

LAST_NAMES = [
    "Sharma",
    "Iyer",
    "Reddy",
    "Kapoor",
    "Nair",
    "Patel",
    "Mehta",
    "Joshi",
    "Rao",
    "Singh",
    "Das",
    "Khan",
    "Gupta",
    "Menon",
    "Bose",
]

TITLE_PATTERNS = [
    "How I built a {topic} workflow with {tag}",
    "Lessons from scaling {topic} in production",
    "A practical guide to {topic} for growing teams",
    "What changed when we redesigned our {topic} stack",
    "Debugging {topic}: mistakes I stopped making",
    "From prototype to production with {topic}",
    "The hidden tradeoffs behind {topic}",
    "A beginner friendly path into {topic}",
    "How to think about {topic} before writing code",
    "Patterns that made our {topic} system easier to maintain",
]

TOPICS_BY_CATEGORY = {
    "Backend Development": ["FastAPI services", "REST APIs", "authentication", "background jobs"],
    "Frontend Engineering": ["component systems", "state management", "forms", "responsive layouts"],
    "Applied AI": ["LLM apps", "prompt pipelines", "semantic search", "recommendation systems"],
    "Data Engineering": ["ETL pipelines", "batch jobs", "data quality", "warehouse modeling"],
    "Cloud Infrastructure": ["cloud deployments", "container platforms", "autoscaling", "observability"],
    "Cybersecurity": ["API security", "token storage", "password handling", "threat modeling"],
    "DevOps": ["CI pipelines", "release automation", "logging", "incident response"],
    "Product Thinking": ["feature prioritization", "feedback loops", "user research", "metrics"],
    "Career Growth": ["learning plans", "portfolio projects", "technical interviews", "mentorship"],
    "Database Design": ["indexes", "schema design", "query planning", "transactions"],
    "System Design": ["feeds", "rate limiting", "caching", "distributed systems"],
    "Machine Learning": ["model evaluation", "feature engineering", "ranking", "experiments"],
}

CONTENT_SNIPPETS = [
    "The main lesson is to keep the first version boring enough to debug.",
    "A clear schema gave the rest of the team a shared language.",
    "The final implementation was smaller after we removed assumptions from the first draft.",
    "Instrumentation mattered because intuition was not enough once usage grew.",
    "The best improvement came from designing the fallback path before the happy path.",
    "I kept the interface narrow so the feature could evolve without touching every caller.",
    "Testing the edge cases early saved a surprising amount of time later.",
    "Small product choices changed the technical design more than the framework did.",
]

COMMENT_TEXTS = [
    "This is useful, thanks for sharing.",
    "I ran into the same issue last week.",
    "The tradeoff section helped a lot.",
    "Would love to see a follow-up with benchmarks.",
    "This made the concept much clearer.",
    "Nice breakdown of the implementation details.",
]

REPORT_REASONS = ["spam", "misleading", "duplicate", "low-quality"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_schema() -> None:
    models.Base.metadata.create_all(bind=engine)
    migrations.run_startup_migrations(engine)


def get_or_create_category(db: Session, name: str) -> models.Category:
    category = db.query(models.Category).filter(models.Category.name == name).first()
    if category:
        return category

    category = models.Category(name=name, slug=slugify(name))
    db.add(category)
    db.flush()
    return category


def get_or_create_tag(db: Session, name: str) -> models.Tag:
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if tag:
        return tag

    tag = models.Tag(name=name, slug=slugify(name))
    db.add(tag)
    db.flush()
    return tag


def get_or_create_user(
    db: Session,
    *,
    email: str,
    name: str,
    role: str,
    password_hash: str,
    bio: str,
    avatar_seed: str,
) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user

    user = models.User(
        name=name,
        email=email,
        password=password_hash,
        role=role,
        bio=bio,
        avatar_url=f"https://api.dicebear.com/7.x/initials/svg?seed={avatar_seed}",
        is_active=True,
        created_at=utc_now() - timedelta(days=random.randint(1, 900)),
    )
    db.add(user)
    db.flush()
    return user


def seed_taxonomy(db: Session) -> tuple[list[models.Category], list[models.Tag]]:
    categories = [get_or_create_category(db, name) for name in CATEGORIES]
    tags = [get_or_create_tag(db, name) for name in TAGS]
    db.commit()
    return categories, tags


def seed_users(db: Session, *, target_users: int, password: str) -> list[models.User]:
    password_hash = PasswordHasher.hash_password(password)

    reader = get_or_create_user(
        db,
        email=SEED_READER_EMAIL,
        name="Seed Reader",
        role="reader",
        password_hash=password_hash,
        bio="A generated reader account used for testing personalized feeds.",
        avatar_seed="Seed Reader",
    )

    authors: list[models.User] = []
    for number in range(1, target_users + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last} {number:03d}"
        role = "admin" if number <= 3 else "author"
        user = get_or_create_user(
            db,
            email=SEED_USER_EMAIL_TEMPLATE.format(number=number),
            name=name,
            role=role,
            password_hash=password_hash,
            bio=f"Writes about {random.choice(CATEGORIES).lower()} and practical software projects.",
            avatar_seed=name,
        )
        authors.append(user)

        if number % 50 == 0:
            db.commit()

    db.commit()
    print(f"Seed users ready: {len(authors)} authors + reader {reader.email}")
    return authors


def build_content(category_name: str, topic: str, selected_tags: list[models.Tag]) -> str:
    tag_text = ", ".join(tag.name for tag in selected_tags)
    paragraphs = [
        f"This post explores {topic} in the context of {category_name.lower()}.",
        random.choice(CONTENT_SNIPPETS),
        f"The implementation used ideas around {tag_text} and focused on keeping the code easy to change.",
        random.choice(CONTENT_SNIPPETS),
        "For a team project, the important part is not only making it work once, but making it explainable.",
    ]
    return "\n\n".join(paragraphs)


def seed_blogs(
    db: Session,
    *,
    target_blogs: int,
    authors: list[models.User],
    categories: list[models.Category],
    tags: list[models.Tag],
) -> list[models.Blog]:
    existing_seed_count = (
        db.query(models.Blog)
        .filter(models.Blog.slug.like(f"{SEED_POST_SLUG_PREFIX}%"))
        .count()
    )

    if existing_seed_count >= target_blogs:
        blogs = (
            db.query(models.Blog)
            .filter(models.Blog.slug.like(f"{SEED_POST_SLUG_PREFIX}%"))
            .all()
        )
        print(f"Seed blogs already ready: {existing_seed_count}")
        return blogs

    start = existing_seed_count + 1
    now = utc_now()
    created_blogs: list[models.Blog] = []

    for number in range(start, target_blogs + 1):
        category = random.choice(categories)
        topic = random.choice(TOPICS_BY_CATEGORY.get(category.name, [category.name.lower()]))
        selected_tags = random.sample(tags, random.randint(2, 5))
        title = random.choice(TITLE_PATTERNS).format(topic=topic, tag=selected_tags[0].name)
        title = f"{title} #{number:04d}"
        created_at = now - timedelta(days=random.randint(0, 540), hours=random.randint(0, 23))

        blog = models.Blog(
            title=title,
            slug=f"{SEED_POST_SLUG_PREFIX}{number:05d}-{slugify(title)[:70]}",
            content=build_content(category.name, topic, selected_tags),
            cover_image_url=f"https://picsum.photos/seed/blog-{number}/1200/630",
            is_public=random.random() > 0.03,
            is_published=random.random() > 0.08,
            view_count=random.randint(0, 5000),
            share_count=random.randint(0, 300),
            created_at=created_at,
            updated_at=created_at + timedelta(days=random.randint(0, 20)),
            user_id=random.choice(authors).id,
            category=category,
        )
        blog.tags = selected_tags
        db.add(blog)
        created_blogs.append(blog)

        if number % 200 == 0:
            db.commit()
            print(f"Created seed blogs: {number}/{target_blogs}")

    db.commit()
    blogs = (
        db.query(models.Blog)
        .filter(models.Blog.slug.like(f"{SEED_POST_SLUG_PREFIX}%"))
        .all()
    )
    print(f"Seed blogs ready: {len(blogs)}")
    return blogs


def create_follow(
    db: Session,
    follower_id: int,
    following_id: int,
    existing_pairs: set[tuple[int, int]],
) -> bool:
    if follower_id == following_id:
        return False

    pair = (follower_id, following_id)
    if pair in existing_pairs:
        return False

    db.add(models.Follow(follower_id=follower_id, following_id=following_id))
    existing_pairs.add(pair)
    return True


def seed_follows(db: Session, *, authors: list[models.User]) -> None:
    reader = db.query(models.User).filter(models.User.email == SEED_READER_EMAIL).one()
    followed_by_reader = random.sample(authors, min(75, len(authors)))
    follow_pairs = {
        (follower_id, following_id)
        for follower_id, following_id in db.query(
            models.Follow.follower_id,
            models.Follow.following_id,
        ).all()
    }
    created = 0

    for author in followed_by_reader:
        created += int(create_follow(db, reader.id, author.id, follow_pairs))

    for author in authors:
        for target in random.sample(authors, min(random.randint(4, 12), len(authors))):
            created += int(create_follow(db, author.id, target.id, follow_pairs))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    print(f"Follow graph ready: added up to {created} new follows")


def seed_interactions(
    db: Session,
    *,
    authors: list[models.User],
    blogs: list[models.Blog],
    likes: int,
    bookmarks: int,
    comments: int,
    reports: int,
) -> None:
    visible_blogs = [blog for blog in blogs if blog.is_public and blog.is_published]
    if not visible_blogs:
        print("No visible blogs found for interactions")
        return

    users = authors + [db.query(models.User).filter(models.User.email == SEED_READER_EMAIL).one()]
    user_ids = [user.id for user in users]
    visible_blog_ids = [blog.id for blog in visible_blogs]
    like_pairs = {
        (user_id, blog_id)
        for user_id, blog_id in db.query(models.Like.user_id, models.Like.blog_id)
        .filter(models.Like.user_id.in_(user_ids), models.Like.blog_id.in_(visible_blog_ids))
        .all()
    }
    bookmark_pairs = {
        (user_id, blog_id)
        for user_id, blog_id in db.query(models.Bookmark.user_id, models.Bookmark.blog_id)
        .filter(models.Bookmark.user_id.in_(user_ids), models.Bookmark.blog_id.in_(visible_blog_ids))
        .all()
    }
    existing_comments = (
        db.query(models.Comment)
        .filter(models.Comment.user_id.in_(user_ids), models.Comment.blog_id.in_(visible_blog_ids))
        .count()
    )
    existing_reports = (
        db.query(models.Report)
        .filter(
            models.Report.reporter_id.in_(user_ids),
            models.Report.blog_id.in_(visible_blog_ids),
            models.Report.details == "Generated moderation test report.",
        )
        .count()
    )
    likes_to_create = max(0, likes - len(like_pairs))
    bookmarks_to_create = max(0, bookmarks - len(bookmark_pairs))
    comments_to_create = max(0, comments - existing_comments)
    reports_to_create = max(0, reports - existing_reports)
    created_likes = 0
    created_bookmarks = 0
    created_comments = 0
    created_reports = 0

    attempts = 0
    max_attempts = max(1000, likes * 5)
    while created_likes < likes_to_create and attempts < max_attempts:
        attempts += 1
        user = random.choice(users)
        blog = random.choice(visible_blogs)
        if user.id == blog.user_id:
            continue
        pair = (user.id, blog.id)
        if pair not in like_pairs:
            db.add(models.Like(user_id=user.id, blog_id=blog.id))
            like_pairs.add(pair)
            created_likes += 1

    attempts = 0
    max_attempts = max(1000, bookmarks * 5)
    while created_bookmarks < bookmarks_to_create and attempts < max_attempts:
        attempts += 1
        user = random.choice(users)
        blog = random.choice(visible_blogs)
        pair = (user.id, blog.id)
        if pair not in bookmark_pairs:
            db.add(models.Bookmark(user_id=user.id, blog_id=blog.id))
            bookmark_pairs.add(pair)
            created_bookmarks += 1

    db.commit()

    for index in range(comments_to_create):
        user = random.choice(users)
        blog = random.choice(visible_blogs)
        db.add(
            models.Comment(
                content=random.choice(COMMENT_TEXTS),
                blog_id=blog.id,
                user_id=user.id,
                created_at=utc_now() - timedelta(days=random.randint(0, 180)),
            )
        )
        created_comments += 1
        if index and index % 300 == 0:
            db.commit()

    attempts = 0
    max_attempts = max(1000, reports * 10)
    while created_reports < reports_to_create and attempts < max_attempts:
        attempts += 1
        user = random.choice(users)
        blog = random.choice(visible_blogs)
        if user.id == blog.user_id:
            continue
        db.add(
            models.Report(
                reason=random.choice(REPORT_REASONS),
                details="Generated moderation test report.",
                blog_id=blog.id,
                reporter_id=user.id,
            )
        )
        created_reports += 1

    db.commit()
    print(
        "Interactions ready: "
        f"{created_likes} likes, "
        f"{created_bookmarks} bookmarks, "
        f"{created_comments} comments, "
        f"{created_reports} reports"
    )


def print_summary(db: Session) -> None:
    visible_blogs = (
        db.query(models.Blog)
        .filter(models.Blog.is_public == True, models.Blog.is_published == True)
        .count()
    )
    reader = db.query(models.User).filter(models.User.email == SEED_READER_EMAIL).one()
    followed_count = (
        db.query(models.Follow)
        .filter(models.Follow.follower_id == reader.id)
        .count()
    )
    following_feed_count = (
        db.query(models.Blog)
        .join(models.Follow, models.Follow.following_id == models.Blog.user_id)
        .filter(
            models.Follow.follower_id == reader.id,
            models.Blog.is_public == True,
            models.Blog.is_published == True,
        )
        .count()
    )

    print("\nSeed summary")
    print("------------")
    print(f"Users: {db.query(models.User).count()}")
    print(f"Blogs: {db.query(models.Blog).count()}")
    print(f"Visible published blogs: {visible_blogs}")
    print(f"Categories: {db.query(models.Category).count()}")
    print(f"Tags: {db.query(models.Tag).count()}")
    print(f"Follows: {db.query(models.Follow).count()}")
    print(f"Likes: {db.query(models.Like).count()}")
    print(f"Bookmarks: {db.query(models.Bookmark).count()}")
    print(f"Comments: {db.query(models.Comment).count()}")
    print(f"Reports: {db.query(models.Report).count()}")
    print(f"Feed test user: {SEED_READER_EMAIL}")
    print("Feed test password: SeedPass123")
    print(f"Feed test user follows: {followed_count} authors")
    print(f"Feed posts available for test user: {following_feed_count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed sample data for the Blog API.")
    parser.add_argument("--users", type=int, default=200, help="Target number of generated author users.")
    parser.add_argument("--blogs", type=int, default=2000, help="Target number of generated seed blog posts.")
    parser.add_argument("--likes", type=int, default=6000, help="Target number of generated likes.")
    parser.add_argument("--bookmarks", type=int, default=2500, help="Target number of generated bookmarks.")
    parser.add_argument("--comments", type=int, default=1200, help="Target number of generated comments.")
    parser.add_argument("--reports", type=int, default=80, help="Target number of generated moderation reports.")
    parser.add_argument("--password", default="SeedPass123", help="Password for generated seed accounts.")
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for repeatable data.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.random_seed)
    ensure_schema()

    db = SessionLocal()
    try:
        categories, tags = seed_taxonomy(db)
        authors = seed_users(db, target_users=args.users, password=args.password)
        blogs = seed_blogs(
            db,
            target_blogs=args.blogs,
            authors=authors,
            categories=categories,
            tags=tags,
        )
        seed_follows(db, authors=authors)
        seed_interactions(
            db,
            authors=authors,
            blogs=blogs,
            likes=args.likes,
            bookmarks=args.bookmarks,
            comments=args.comments,
            reports=args.reports,
        )
        print_summary(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
