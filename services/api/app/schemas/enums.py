from enum import Enum


class AIAssessmentEnum(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    NOT_VISIBLE = "not_visible"
    CHANGED = "changed"
    UNCERTAIN = "uncertain"


class ReviewStatusEnum(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    NOT_ISSUE = "not_issue"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class ModelAssessmentEnum(str, Enum):
    CLEAR = "clear"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"


class PriorityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SeverityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PolicyRuleStatusEnum(str, Enum):
    EXTRACTED = "extracted"
    APPROVED = "approved"
    REJECTED = "rejected"


class PolicyDocumentStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class AnalysisRunStatusEnum(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ClipRoleEnum(str, Enum):
    REFERENCE = "reference"
    COMPARISON = "comparison"


class FindingTypeEnum(str, Enum):
    CONTINUITY = "continuity"
    VISUAL_REVIEW = "visual_review"


class ErrorCodeEnum(str, Enum):
    UPLOAD_FAILED = "UPLOAD_FAILED"
    PARSE_FAILED = "PARSE_FAILED"
    GEMINI_TIMEOUT = "GEMINI_TIMEOUT"
    INVALID_GEMINI_OUTPUT = "INVALID_GEMINI_OUTPUT"
    MEDIA_PROCESSING_FAILED = "MEDIA_PROCESSING_FAILED"
    MCP_UNAVAILABLE = "MCP_UNAVAILABLE"
    QUERY_REJECTED = "QUERY_REJECTED"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    INVALID_TRANSITION = "INVALID_TRANSITION"


def derive_severity(priority: PriorityEnum) -> SeverityEnum:
    """Derives finding severity deterministically from matched policy rule priority."""
    return SeverityEnum(priority.value)


VALID_STATUS_TRANSITIONS: dict[ReviewStatusEnum, set[ReviewStatusEnum]] = {
    ReviewStatusEnum.OPEN: {
        ReviewStatusEnum.OPEN,
        ReviewStatusEnum.CONFIRMED,
        ReviewStatusEnum.NOT_ISSUE,
        ReviewStatusEnum.ESCALATED,
    },
    ReviewStatusEnum.CONFIRMED: {
        ReviewStatusEnum.CONFIRMED,
        ReviewStatusEnum.RESOLVED,
    },
    ReviewStatusEnum.ESCALATED: {
        ReviewStatusEnum.ESCALATED,
        ReviewStatusEnum.RESOLVED,
    },
    ReviewStatusEnum.NOT_ISSUE: {
        ReviewStatusEnum.NOT_ISSUE,
    },
    ReviewStatusEnum.RESOLVED: {
        ReviewStatusEnum.RESOLVED,
    },
}


def validate_review_status_transition(
    current: ReviewStatusEnum, new_status: ReviewStatusEnum
) -> bool:
    """Validates state transitions for review_status in the decisions log."""
    allowed = VALID_STATUS_TRANSITIONS.get(current, set())
    return new_status in allowed

