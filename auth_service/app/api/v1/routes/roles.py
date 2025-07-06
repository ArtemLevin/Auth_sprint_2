from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (get_current_user, rate_limit_dependency,
                                   require_permission)
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.error import ErrorResponseModel
from app.schemas.permission import UserPermissionsResponse
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.role_service import RoleService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/roles", tags=["Roles"])


async def get_role_service(db: AsyncSession = Depends(get_db_session)) -> RoleService:
    return RoleService(db)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def create_role(
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
):
    try:
        role = await role_service.create_role(role_data)
        logger.info("Роль успешно создана", role_name=role.name, role_id=role.id)
        return role
    except ValueError as e:
        logger.error(
            "Ошибка при создании роли", detail=str(e), role_name=role_data.name
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/",
    response_model=list[RoleResponse],
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(get_current_user), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def get_all_roles(
    role_service: RoleService = Depends(get_role_service),
):
    roles = await role_service.get_all_roles()
    logger.info("Получен список всех ролей", count=len(roles))
    return roles


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(get_current_user), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def get_role_by_id(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.get_role_by_id(role_id)
    if not role:
        logger.warning("Роль не найдена", role_id=role_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    logger.info("Роль успешно получена", role_id=role_id)
    return role


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseModel},
        status.HTTP_409_CONFLICT: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def update_role(
    role_id: UUID,
    role_update: RoleUpdate,
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.update_role(role_id, role_update)
    if not role:
        logger.warning("Роль не найдена для обновления", role_id=role_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    logger.info("Роль успешно обновлена", role_id=role.id, updated_fields=role_update.model_dump(exclude_unset=True).keys())
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),

):
    deleted = await role_service.delete_role(role_id)
    if not deleted:
        logger.warning("Роль не найдена для удаления", role_id=role_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    logger.info("Роль успешно удалена", role_id=role_id)
    return {"message": "Role deleted successfully"}


@router.post(
    "/{role_id}/assign/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def assign_role_to_user(
    role_id: UUID,
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    assigned = await role_service.assign_role_to_user(user_id, role_id)
    if not assigned:
        logger.warning(
            "Не удалось назначить роль пользователю", user_id=user_id, role_id=role_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User or Role not found, or role already assigned",
        )
    logger.info("Роль успешно назначена пользователю", user_id=user_id, role_id=role_id)
    return {"message": "Role assigned successfully"}


@router.delete(
    "/{role_id}/revoke/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def revoke_role_from_user(
    role_id: UUID,
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    revoked = await role_service.revoke_role_from_user(user_id, role_id)
    if not revoked:
        logger.warning(
            "Не удалось отозвать роль у пользователя", user_id=user_id, role_id=role_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User-Role assignment not found",
        )
    logger.info(
        "Роль успешно отозвана у пользователя", user_id=user_id, role_id=role_id
    )
    return {"message": "Role revoked successfully"}


@router.get(
    "/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseModel},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Too many requests",
            "model": ErrorResponseModel,
        },
    },
    dependencies=[Depends(require_permission("manage_roles")), Depends(lambda: rate_limit_dependency(traffic_type="default"))]
)
async def get_user_permissions_endpoint(
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    db: AsyncSession = Depends(get_db_session),
):
    user_obj = await db.get(User, user_id)
    if not user_obj:
        logger.warning(
            "Пользователь не найден для получения разрешений", user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    permissions = await role_service.get_user_permissions(user_id)
    logger.info(
        "Получены разрешения для пользователя", user_id=user_id, permissions=permissions
    )
    return UserPermissionsResponse(user_id=user_id, permissions=permissions)