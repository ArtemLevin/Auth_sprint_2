from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Union, List, Any
from uuid import UUID

from auth_service.app.settings import settings
from auth_service.app.utils.cache import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_jti() -> str:
    import uuid

    return str(uuid.uuid4())


def create_access_token(
    subject: Union[str, UUID],
    payload: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
    mfa_verified: bool = False,
) -> str:
    to_encode = payload.copy() if payload else {}
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    jti = generate_jti()
    to_encode.update(
        {"exp": expire, "sub": str(subject), "jti": jti, "mfa_verified": mfa_verified}
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, UUID],
    payload: Optional[Dict[str, Any]] = None,
    expires_days: Optional[int] = None,
) -> str:
    to_encode = payload.copy() if payload else {}
    expire = datetime.now(timezone.utc) + timedelta(
        days=expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    jti = generate_jti()
    to_encode.update({"exp": expire, "sub": str(subject), "jti": jti})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_REFRESH_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


async def is_token_blacklisted(jti: str) -> bool:
    blacklisted = await redis_client.get(f"blacklist:{jti}")
    return blacklisted is not None


async def add_to_blacklist(jti: str, ttl_seconds: int):
    await redis_client.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def decode_jwt(
    token: str, refresh: bool = False, options: Optional[Dict] = None
) -> Dict:
    secret = (
        settings.JWT_REFRESH_SECRET_KEY.get_secret_value()
        if refresh
        else settings.JWT_SECRET_KEY.get_secret_value()
    )
    decoded = jwt.decode(
        token, secret, algorithms=[settings.JWT_ALGORITHM], options=options or {}
    )

    jti = decoded.get("jti")
    if jti and not refresh:
        if await is_token_blacklisted(jti):
            raise ValueError("Token is blacklisted")

    return decoded
