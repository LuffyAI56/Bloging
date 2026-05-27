from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_column(engine: Engine, table_name: str, column_name: str, ddl: str):
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(table_name)}

    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def run_startup_migrations(engine: Engine):
    ensure_column(engine, "users", "role", "role VARCHAR DEFAULT 'author'")
    ensure_column(engine, "users", "bio", "bio TEXT")
    ensure_column(engine, "users", "avatar_url", "avatar_url VARCHAR")
    ensure_column(engine, "users", "is_active", "is_active BOOLEAN DEFAULT 1")
    ensure_column(engine, "users", "created_at", "created_at DATETIME")
    ensure_column(engine, "users", "updated_at", "updated_at DATETIME")

    ensure_column(engine, "blogs", "slug", "slug VARCHAR")
    ensure_column(engine, "blogs", "cover_image_url", "cover_image_url VARCHAR")
    ensure_column(engine, "blogs", "is_public", "is_public BOOLEAN DEFAULT 1")
    ensure_column(engine, "blogs", "is_published", "is_published BOOLEAN DEFAULT 1")
    ensure_column(engine, "blogs", "view_count", "view_count INTEGER DEFAULT 0")
    ensure_column(engine, "blogs", "share_count", "share_count INTEGER DEFAULT 0")
    ensure_column(engine, "blogs", "category_id", "category_id INTEGER")
    ensure_column(engine, "blogs", "created_at", "created_at DATETIME")
    ensure_column(engine, "blogs", "updated_at", "updated_at DATETIME")
