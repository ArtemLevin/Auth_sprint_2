from pydantic import BaseModel
from typing import Optional

class MFASetupResponse(BaseModel):
    qr_code: str

class MFAVerifyRequest(BaseModel):
    code: str

class MFAVerifyResponse(BaseModel):
    status: str = "success"
    token: Optional[dict] = None