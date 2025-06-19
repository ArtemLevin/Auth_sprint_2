from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.app.utils.auth import authenticate_user, create_access_token, create_refresh_token
from auth_service.app.db.session import get_db_session
from auth_service.app.schemas import TokenPair


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenPair)
async def login(login: str, password: str, db: AsyncSession = Depends(get_db_session)):
    user = await authenticate_user(login, password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect login or password")

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return {"access_token": access_token, "refresh_token": refresh_token}

