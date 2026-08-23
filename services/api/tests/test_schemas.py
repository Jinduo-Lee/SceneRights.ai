from datetime import datetime
import pytest
from pydantic import ValidationError
from app.schemas.enums import (
    AIAssessmentEnum,
    AnalysisRunStatusEnum,
    ClipRoleEnum,
    ErrorCodeEnum,
    FindingTypeEnum,
    ModelAssessmentEnum,
    PolicyDocumentStatusEnum,
    PolicyRuleStatusEnum,
    PriorityEnum,
    ReviewStatusEnum,
    SeverityEnum,
    derive_severity,
    validate_review_status_transition,
)
from app.schemas.policy import PolicyDocument, PolicyRule
from app.schemas.scene import Clip, Scene
from app.schemas.analysis import AnalysisRun
from app.schemas.finding import Decision, Finding
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse, ToolCallSummary


def test_enum_exact_values():
    assert set(e.value for e in AIAssessmentEnum) == {
        "present",
        "absent",
        "not_visible",
        "changed",
        "uncertain",
    }
    assert set(e.value for e in ReviewStatusEnum) == {
        "open",
        "confirmed",
        "not_issue",
        "escalated",
        "resolved",
    }
    assert set(e.value for e in ModelAssessmentEnum) == {
        "clear",
        "likely",
        "uncertain",
    }
    assert set(e.value for e in PriorityEnum) == {"high", "medium", "low"}
    assert set(e.value for e in SeverityEnum) == {"high", "medium", "low"}
    assert set(e.value for e in PolicyRuleStatusEnum) == {
        "extracted",
        "approved",
        "rejected",
    }
    assert set(e.value for e in PolicyDocumentStatusEnum) == {
        "uploaded",
        "processing",
        "ready",
        "failed",
    }
    assert set(e.value for e in AnalysisRunStatusEnum) == {
        "queued",
        "running",
        "succeeded",
        "failed",
    }
    assert set(e.value for e in ClipRoleEnum) == {"reference", "comparison"}
    assert set(e.value for e in FindingTypeEnum) == {"continuity", "visual_review"}


def test_invalid_enum_rejection():
    with pytest.raises(ValueError):
        AIAssessmentEnum("invalid_assessment")

    with pytest.raises(ValueError):
        ReviewStatusEnum("awaiting_review")  # old v6 legacy vocabulary rejected

    with pytest.raises(ValueError):
        ModelAssessmentEnum("95%")  # no percentage allowed


def test_severity_derivation():
    assert derive_severity(PriorityEnum.HIGH) == SeverityEnum.HIGH
    assert derive_severity(PriorityEnum.MEDIUM) == SeverityEnum.MEDIUM
    assert derive_severity(PriorityEnum.LOW) == SeverityEnum.LOW


def test_review_status_transitions():
    # Valid transitions
    assert validate_review_status_transition(ReviewStatusEnum.OPEN, ReviewStatusEnum.CONFIRMED) is True
    assert validate_review_status_transition(ReviewStatusEnum.OPEN, ReviewStatusEnum.NOT_ISSUE) is True
    assert validate_review_status_transition(ReviewStatusEnum.OPEN, ReviewStatusEnum.ESCALATED) is True
    assert validate_review_status_transition(ReviewStatusEnum.CONFIRMED, ReviewStatusEnum.RESOLVED) is True
    assert validate_review_status_transition(ReviewStatusEnum.ESCALATED, ReviewStatusEnum.RESOLVED) is True
    assert validate_review_status_transition(ReviewStatusEnum.OPEN, ReviewStatusEnum.OPEN) is True

    # Invalid transitions
    assert validate_review_status_transition(ReviewStatusEnum.RESOLVED, ReviewStatusEnum.OPEN) is False
    assert validate_review_status_transition(ReviewStatusEnum.CONFIRMED, ReviewStatusEnum.OPEN) is False
    assert validate_review_status_transition(ReviewStatusEnum.NOT_ISSUE, ReviewStatusEnum.RESOLVED) is False


def test_policy_document_dto():
    now = datetime.now()
    doc = PolicyDocument(
        project_id="project_001",
        policy_id="policy_123",
        filename="northstar_policy.pdf",
        gcs_uri="gs://bucket/northstar_policy.pdf",
        status=PolicyDocumentStatusEnum.READY,
        created_at=now,
        updated_at=now,
    )
    assert doc.policy_id == "policy_123"
    assert doc.status == PolicyDocumentStatusEnum.READY


def test_policy_rule_dto():
    now = datetime.now()
    rule = PolicyRule(
        project_id="project_001",
        policy_id="policy_123",
        policy_rule_id="rule_001",
        document_name="northstar_policy.pdf",
        policy_type="continuity",
        rule_text="Hero mug remains blue throughout Scene 12.",
        source_quote="Hero mug remains blue throughout Scene 12.",
        priority=PriorityEnum.HIGH,
        status=PolicyRuleStatusEnum.APPROVED,
        version=1,
        created_at=now,
    )
    assert rule.policy_id == "policy_123"
    assert rule.policy_rule_id == "rule_001"
    assert rule.priority == PriorityEnum.HIGH


def test_scene_and_clip_dtos():
    now = datetime.now()
    scene = Scene(
        project_id="project_001",
        scene_id="scene_12",
        name="Scene 12",
        reference_clip_id="take_a",
        created_at=now,
    )
    clip = Clip(
        project_id="project_001",
        clip_id="take_a",
        scene_id="scene_12",
        role=ClipRoleEnum.REFERENCE,
        gcs_uri="gs://bucket/take_a.mp4",
        created_at=now,
    )
    assert scene.scene_id == "scene_12"
    assert clip.role == ClipRoleEnum.REFERENCE


def test_analysis_run_dto():
    now = datetime.now()
    run = AnalysisRun(
        project_id="project_001",
        scene_id="scene_12",
        analysis_run_id="run_456",
        status=AnalysisRunStatusEnum.SUCCEEDED,
        step="completed",
        started_at=now,
        completed_at=now,
        findings_count=2,
    )
    assert run.status == AnalysisRunStatusEnum.SUCCEEDED
    assert run.findings_count == 2


def test_finding_and_decision_dtos():
    now = datetime.now()
    finding = Finding(
        project_id="project_001",
        scene_id="scene_12",
        finding_id="find_001",
        analysis_run_id="run_456",
        finding_type=FindingTypeEnum.CONTINUITY,
        object_type="mug",
        object_label="hero blue mug",
        reference_clip="take_a",
        comparison_clip="take_b",
        ai_assessment=AIAssessmentEnum.CHANGED,
        model_assessment=ModelAssessmentEnum.CLEAR,
        severity=SeverityEnum.HIGH,
        policy_rule_id="rule_002",
        policy_rule_version=1,
        policy_document="northstar_policy.pdf",
        policy_rule="Hero mug remains blue throughout Scene 12.",
        source_quote="Hero mug remains blue throughout Scene 12.",
        timestamp_ms=12000,
        created_at=now,
        review_status=ReviewStatusEnum.OPEN,
    )
    assert finding.ai_assessment == AIAssessmentEnum.CHANGED
    assert finding.review_status == ReviewStatusEnum.OPEN

    decision = Decision(
        project_id="project_001",
        finding_id="find_001",
        review_status=ReviewStatusEnum.CONFIRMED,
        previous_status=ReviewStatusEnum.OPEN,
        reviewer="script_supervisor_01",
        comment="Confirmed mug colour changed to red",
        created_at=now,
    )
    assert decision.review_status == ReviewStatusEnum.CONFIRMED


def test_agent_query_dtos():
    req = AgentQueryRequest(
        project_id="project_001",
        scene_id="scene_12",
        message="What unresolved issues remain?",
    )
    tool_call = ToolCallSummary(
        tool="clickhouse_mcp",
        sql_summary="SELECT * FROM findings_current WHERE review_status IN ('open', 'escalated')",
        row_count=2,
        latency_ms=145,
        status="success",
    )
    resp = AgentQueryResponse(
        answer="Scene 12 has two unresolved findings.",
        tool_calls=[tool_call],
    )
    assert req.scene_id == "scene_12"
    assert resp.tool_calls[0].row_count == 2
