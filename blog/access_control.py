"""
Access control definitions and RBAC (Role-Based Access Control) dependencies.
"""
from enum import IntEnum

from fastapi import Depends, HTTPException, status

from . import schemas
from .oauth2 import get_current_user


class AccessLevel(IntEnum):
    """Defines hierarchical access levels for roles."""
    READER = 1
    AUTHOR = 2
    ADMIN = 3


# Map user role strings to AccessLevel integers
ROLE_ACCESS_LEVELS = {
    "reader": AccessLevel.READER,
    "author": AccessLevel.AUTHOR,
    "admin": AccessLevel.ADMIN,
}


def require_access_level(required_level: AccessLevel):
    """
    Creates a FastAPI dependency that enforces a minimum access level.
    Users with a role lower than the required level will receive a 403 Forbidden.
    """
    def access_checker(
        current_user: schemas.TokenData = Depends(get_current_user),
    ) -> schemas.TokenData:
        user_level = ROLE_ACCESS_LEVELS.get(current_user.role)

        # Check if user has sufficient privileges
        if user_level is None or user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough access"
            )

        return current_user

    return access_checker
