from fastapi import APIRouter, Depends, HTTPException
from auth_service.app.schemas.role import RoleCreate, RoleResponse
from auth_service.app.services.role_service import RoleService
from auth_service.app.core.dependencies import get_current_user

from auth_service.app.core.middleware import require_permission

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.post("/", response_model=RoleResponse)
async def create_role(role: RoleCreate, user: dict = Depends(require_permission("manage_roles"))):
    return await RoleService.create_role(role)

@router.get("/", response_model=list[RoleResponse])
async def get_all_roles(user: dict = Depends(get_current_user)):
    return await RoleService.get_all_roles()

@router.delete("/{role_id}")
async def delete_role(role_id: str, user: dict = Depends(require_permission("manage_roles"))):
    await RoleService.delete_role(role_id)
    return {"message": "Role deleted"}