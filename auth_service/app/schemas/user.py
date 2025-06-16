from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Annotated
from annotated_types import MaxLen, MinLen


class UserBase(BaseModel):
    login: Annotated[str, MaxLen(50)]
    email: Optional[Annotated[str, MaxLen(100)]] = None


class UserCreate(UserBase):
    password: Annotated[str, MinLen(6)]


class UpdateProfileRequest(BaseModel):
    login: Optional[Annotated[str, MaxLen(50)]] = None
    password: Optional[Annotated[str, MinLen(6)]] = None


class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)