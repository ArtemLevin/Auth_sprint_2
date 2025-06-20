from typing import List

from pydantic import BaseModel


class PermissionCheckRequest(BaseModel):
    user_id: str
    required_permission: str


class PermissionCheckResponse(BaseModel):
    has_access: bool
    missing_permissions: List[str] = []
