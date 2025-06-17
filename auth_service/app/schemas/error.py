from pydantic import BaseModel
from typing import Optional, Dict

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    meta: Dict = {"status": "error"}

class SuccessResponse(BaseModel):
    data: dict
    meta: Dict = {"status": "success"}