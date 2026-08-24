from datetime import datetime
from typing import Optional
from pydantic import BaseModel
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

