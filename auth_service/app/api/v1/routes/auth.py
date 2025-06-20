from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.app.utils.auth import authenticate_user
from auth_service.app.core.security import create_access_token, create_refresh_token
from auth_service.app.db.session import get_db_session
from auth_service.app.schemas import TokenPair, LoginRequest
from auth_service.app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenPair)
async def login(request_data: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    user: User | None = await authenticate_user(request_data.login, request_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect login or password")

    access_token = create_access_token(subject=user.id, payload={"login": user.login})
    refresh_token = create_refresh_token(subject=user.id)

    return {"access_token": access_token, "refresh_token": refresh_token}