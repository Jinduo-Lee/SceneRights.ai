from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.enums import ClipRoleEnum


class Clip(BaseModel):
    project_id: str
    clip_id: str
    scene_id: str
    role: ClipRoleEnum
    gcs_uri: str
    created_at: datetime


class Scene(BaseModel):
    project_id: str
    scene_id: str
    name: str
    reference_clip_id: Optional[str] = None
    created_at: datetime

