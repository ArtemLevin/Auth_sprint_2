from typing import Optional

from pydantic import BaseModel


class MFASetupResponse(BaseModel):
    qr_code: str


class MFAVerifyRequest(BaseModel):
    code: str


class MFAVerifyResponse(BaseModel):
    status: str = "success"
    token: Optional[dict] = None
