from jose import jwt
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth_service.app.settings import settings
from auth_service.app.db.session import get_db_session
from auth_service.app.models.user import User
from auth_service.app.schemas import TokenData

from auth_service.app.core.security import verify_password


async def get_user_from_token(token: str, db: AsyncSession) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_data = TokenData.model_validate(payload)

        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return {"user": user, "payload": payload}
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def authenticate_user(
    login: str, password: str, db: AsyncSession
) -> Optional[User]:
    result = await db.execute(select(User).where(User.login == login))
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
