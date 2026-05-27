"""
Main application entry point for the Blog API.
Initializes FastAPI, sets up CORS, database migrations, and routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import migrations, models
from .config import get_settings
from .database import engine
from .routers import authentication, blog, user

# Load application settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title="Blog API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Add TrustedHostMiddleware to prevent HTTP Host Header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Initialize database schemas and run startup migrations
models.Base.metadata.create_all(bind=engine)
migrations.run_startup_migrations(engine)

# Include API routers
app.include_router(blog.router)
app.include_router(user.router)
app.include_router(authentication.router)
