"""
Provides password hashing utilities using Passlib and bcrypt.
"""
from passlib.context import CryptContext

# Define the password hashing context with bcrypt
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Helper class for hashing and verifying passwords."""
    
    @staticmethod
    def hash_password(password: str):
        """Generates a secure bcrypt hash for a plaintext password."""
        return password_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        """Verifies a plaintext password against a stored hash."""
        return password_context.verify(plain_password, hashed_password)
