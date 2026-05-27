"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

# Use check_same_thread=False for SQLite, otherwise empty args
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# Initialize SQLAlchemy engine
engine = create_engine(settings.database_url, connect_args=connect_args)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for declarative class definitions
Base = declarative_base()


def get_db():
    """
    Dependency function to yield a database session.
    Closes the session after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
