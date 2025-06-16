from app.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.db.session import async_session
from sqlalchemy.future import select
from fastapi import HTTPException

class AuthService:
    @staticmethod
    async def login(login: str, password: str):
        async with async_session() as session:
            result = await session.execute(select(User).where(User.login == login))
            user = result.scalars().first()
            if not user or not verify_password(password, user.password_hash):
                return None
            access_token = create_access_token(subject=user.id, payload={"login": user.login})
            refresh_token = create_refresh_token(subject=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}

    @staticmethod
    async def register(login: str, password: str, email: str = None):
        pass