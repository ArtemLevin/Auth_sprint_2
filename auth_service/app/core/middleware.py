from functools import wraps
from fastapi import Request, HTTPException
from auth_service.app.core.jwt import decode_jwt
from auth_service.app.core.cache import redis_cache

def require_permission(required_permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                raise HTTPException(status_code=401, detail="Missing token")

            decoded = decode_jwt(token)
            user_id = decoded["sub"]

            permissions = await redis_cache.get(f"permissions:{user_id}")
            if not permissions:
                permissions = await fetch_permissions_from_db(user_id)
                await redis_cache.setex(f"permissions:{user_id}", 3600, permissions)

            if required_permission not in permissions:
                raise HTTPException(status_code=403, detail="Access denied")

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator