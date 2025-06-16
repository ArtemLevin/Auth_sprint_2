from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Annotated
from annotated_types import MaxLen, MinLen


class TokenData(BaseModel):
    user_id: str
    exp: Optional[datetime] = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    login: Annotated[str, MinLen(3), MaxLen(50)]
    password: Annotated[str, MinLen(6)]


class RegisterRequest(BaseModel):
    login: Annotated[str, MinLen(3), MaxLen(50)]
    password: Annotated[str, MinLen(6)]
    email: Optional[Annotated[str, MaxLen(100)]] = None
