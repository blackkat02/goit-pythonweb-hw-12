from fastapi import Depends, HTTPException, status
from typing import List
from src.database.models import Role, UserModel
from src.services.auth import get_current_user


class RoleChecker:
    """
    Dependency to check if the current user has one of the required roles.
    """
    def __init__(self, required_roles: List[Role]):
        self.required_roles = required_roles

    async def __call__(self, user: UserModel = Depends(get_current_user)):
        if user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation forbidden: insufficient permissions.",
            )