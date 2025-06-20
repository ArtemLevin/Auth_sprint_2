from fastapi import Depends, HTTPException, Request, status
from typing import Dict, List, Any
from jose import jwt
from auth_service.app.core.security import decode_jwt, is_token_blacklisted
from auth_service.app.utils.cache import redis_client
from auth_service.app.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth_service.app.models import User, Role, UserRole


async def get_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header[7:]


async def get_cached_permissions(user_id: str, db: AsyncSession) -> List[str]:
    permissions_str = await redis_client.get(f"permissions:{user_id}")
    if permissions_str:
        return permissions_str.split(",")

    result = await db.execute(
        select(Role.permissions)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    all_permissions = set()
    for row in result.scalars().all():
        all_permissions.update(row)

    user_result = await db.execute(select(User.is_superuser).where(User.id == user_id))
    is_superuser = user_result.scalar_one_or_none()
    if is_superuser:
        all_permissions.update(
            ["manage_roles", "view_content", "manage_users", "admin_panel"]
        )

    permissions_list = list(all_permissions)
    if permissions_list:
        await redis_client.setex(
            f"permissions:{user_id}", 3600, ",".join(permissions_list)
        )
    return permissions_list if permissions_list else ["view_content"]


async def get_current_user(
    token: str = Depends(get_token), db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    try:
        payload = await decode_jwt(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        user_obj = await db.get(User, user_id)
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        permissions = await get_cached_permissions(user_id, db)

        if user_obj.is_superuser:
            permissions = ["*"]

        return {
            "id": str(user_id),
            "login": payload.get("login", user_obj.login),
            "mfa_verified": payload.get("mfa_verified", False),
            "is_superuser": user_obj.is_superuser,
            "permissions": permissions,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
