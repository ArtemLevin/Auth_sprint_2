from fastapi import Depends, HTTPException, Request
from typing import Dict
from auth_service.app.core.security import decode_jwt
from auth_service.app.utils.cache import redis_client

async def get_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header[7:]


async def get_current_user(token: str = Depends(get_token)) -> Dict[str, str]:
    try:
        payload = decode_jwt(token)

        jti = payload.get("jti")
        if jti:
            blacklisted = await redis_client.get(f"blacklist:{jti}")
            if blacklisted:
                raise HTTPException(status_code=401, detail="Token is blacklisted")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "id": user_id,
            "login": payload.get("login"),
            "mfa_verified": payload.get("mfa_verified", False),
            "permissions": await get_cached_permissions(user_id)
        }

    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_cached_permissions(user_id: str) -> List[str]:
    permissions = await redis_client.get(f"permissions:{user_id}")
    if permissions:
        return permissions.split(",")
    return ["view_content"]