from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.enums import (
    PolicyDocumentStatusEnum,
    PolicyRuleStatusEnum,
    PriorityEnum,
)


class PolicyDocument(BaseModel):
    project_id: str
    policy_id: str
    filename: str
    gcs_uri: str
    status: PolicyDocumentStatusEnum
    created_at: datetime
    updated_at: datetime


class PolicyRule(BaseModel):
    project_id: str
    policy_id: str
    policy_rule_id: str
    document_name: str
    policy_type: str
    rule_text: str
    source_quote: str
    priority: PriorityEnum
    status: PolicyRuleStatusEnum
    version: int = 1
    effective_date: Optional[datetime] = None
    created_at: datetime


class ExtractedRuleItem(BaseModel):
    category: str = Field(description="Policy type category, e.g., 'continuity' or 'visual_review'")
    rule_text: str = Field(description="Normalized enforceable policy rule text")
    source_quote: str = Field(description="Verbatim exact source quote substring from document text")
    priority: PriorityEnum = Field(default=PriorityEnum.HIGH, description="Priority level: high, medium, low")


class ExtractedRuleList(BaseModel):
    rules: List[ExtractedRuleItem]


class PolicyProcessResponse(BaseModel):
    policy_id: str
    status: PolicyDocumentStatusEnum
    rules_extracted: int
    rules: List[PolicyRule]
