from pydantic import BaseModel
from typing import List

class PermissionCheckRequest(BaseModel):
    user_id: str
    required_permission: str

class PermissionCheckResponse(BaseModel):
    has_access: bool
    missing_permissions: List[str] = []