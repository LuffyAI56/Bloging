"""
Utility functions for text manipulation and generation.
"""
import re


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
