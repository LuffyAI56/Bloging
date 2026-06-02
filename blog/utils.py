"""
Utility functions for text manipulation and generation.
"""
import html
import re


def sanitize_text(value: str, max_length: int = 10000) -> str:
    """Normalize and escape text input to prevent HTML injection."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("Expected a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError("Text value must not be empty")
    if len(normalized) > max_length:
        raise ValueError(f"Text value must be at most {max_length} characters")

    return html.escape(normalized)


def slugify(value: str):
    """
    Converts a given string into a URL-friendly slug.
    Replaces non-alphanumeric characters with hyphens.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def unique_slug(db, model, value: str):
    """
    Generates a unique slug for a given SQLAlchemy model.
    Appends an incrementing counter if the generated slug already exists.
    """
    base_slug = slugify(value)
    slug = base_slug
    counter = 2

    # Query the database to ensure slug uniqueness
    while db.query(model).filter(model.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
