from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.schemas.enums import ErrorCodeEnum


class ErrorDetail(BaseModel):
    code: ErrorCodeEnum
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class Project(BaseModel):
    project_id: str
    name: str
    status: str = "active"
    created_at: datetime

