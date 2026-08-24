from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.enums import (
    AIAssessmentEnum,
    FindingTypeEnum,
    ModelAssessmentEnum,
    ReviewStatusEnum,
    SeverityEnum,
)


class Finding(BaseModel):
    project_id: str
    scene_id: str
    finding_id: str
    analysis_run_id: str
    finding_type: FindingTypeEnum
    object_type: str
    object_label: str
    reference_clip: str
    comparison_clip: str
    ai_assessment: AIAssessmentEnum
    model_assessment: ModelAssessmentEnum
    severity: SeverityEnum
    policy_rule_id: str
    policy_rule_version: int = 1
    policy_document: str
    policy_rule: str
    source_quote: str
    timestamp_ms: int = 0
    created_at: datetime
    review_status: ReviewStatusEnum = ReviewStatusEnum.OPEN


class Decision(BaseModel):
    project_id: str
    finding_id: str
    review_status: ReviewStatusEnum
    previous_status: ReviewStatusEnum
    reviewer: str
    comment: Optional[str] = None
    created_at: datetime

