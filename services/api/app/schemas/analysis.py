from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.enums import AnalysisRunStatusEnum


class AnalysisRun(BaseModel):
    project_id: str
    scene_id: str
    analysis_run_id: str
    status: AnalysisRunStatusEnum
    step: str
    error_code: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings_count: Optional[int] = None
