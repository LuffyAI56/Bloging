from functools import lru_cache
from pathlib import Path

def load_env_file(path: str = ".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        import os
        os.environ.setdefault(key, value)


class Settings:
    def __init__(self):
        import os

        load_env_file()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
        self.secret_key = os.getenv("SECRET_KEY") or self._development_secret()
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.allowed_origins = self._csv(os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"))
        self.allowed_hosts = self._csv(os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost"))

        if self.environment == "production" and not os.getenv("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY must be set in production")

    @staticmethod
    def _csv(value: str):
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _development_secret():
        return "development-only-secret-change-before-production"


@lru_cache
def get_settings():
    return Settings()
