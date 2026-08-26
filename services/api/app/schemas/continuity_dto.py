from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.enums import AIAssessmentEnum, ModelAssessmentEnum


class ClipAssessment(BaseModel):
    clip_id: str
    ai_assessment: AIAssessmentEnum


class ContinuityItemAssessment(BaseModel):
    object_type: str = Field(description="Tracked object type, e.g. 'necklace' or 'hero_mug'")
    object_label: str = Field(description="Human readable label")
    reference: ClipAssessment
    comparison: ClipAssessment
    model_assessment: ModelAssessmentEnum = Field(default=ModelAssessmentEnum.CLEAR)


class ContinuityCompareResponse(BaseModel):
    assessments: List[ContinuityItemAssessment]


class AnalyzeResponse(BaseModel):
    analysis_run_id: str
    status: str

