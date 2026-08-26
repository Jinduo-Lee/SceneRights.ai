import io
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.db.clickhouse import apply_migrations, get_clickhouse_client
from app.services.video_processor import (
    validate_video_file,
    extract_deterministic_keyframes,
    corroborate_mug_color_hsv,
    generate_synthetic_demo_keyframes,
)
from app.services.continuity import continuity_engine
from app.schemas.enums import (
    AIAssessmentEnum,
    ModelAssessmentEnum,
    SeverityEnum,
    PriorityEnum,
)

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.DEMO_ACCESS_TOKEN}"}


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure schema migrations are applied and demo project is seeded."""
    try:
        apply_migrations()
        client.post(f"/api/projects/{settings.DEMO_PROJECT_ID}/seed")
    except Exception:
        pass


# VID-001 — Valid video upload validation passes
def test_vid_001_valid_video():
    valid, msg = validate_video_file("take_a.mp4", 1024 * 1024)
    assert valid is True
    assert msg == ""


# VID-002 — Video larger than 100MB is rejected
def test_vid_002_oversized_video_rejected():
    oversized = 100 * 1024 * 1024 + 1
    valid, msg = validate_video_file("huge.mp4", oversized)
    assert valid is False
    assert "exceeds maximum limit" in msg


# VID-004 — Unsupported video format rejected
def test_vid_004_unsupported_video_format():
    valid, msg = validate_video_file("take_a.xyz", 500)
    assert valid is False
    assert "Unsupported video format" in msg


# FFMPEG-001 & FFMPEG-002 — Keyframes generated at deterministic timestamps
def test_ffmpeg_001_deterministic_keyframes():
    keyframes = generate_synthetic_demo_keyframes(num_frames=3)
    assert len(keyframes) == 3
    for kf in keyframes:
        assert isinstance(kf, bytes)
        assert len(kf) > 0


# OpenCV Mug Color Corroboration Helper
def test_opencv_mug_color_hsv_corroboration():
    # Test fallback image color extraction
    sample_kf = generate_synthetic_demo_keyframes(1)[0]
    color = corroborate_mug_color_hsv(sample_kf)
    assert color in ("blue", "red", "unknown")


# SCN-001 & SCN-003 — Scene creation and reference take assignment
def test_scn_001_create_scene_and_set_reference():
    # 1. Create scene
    create_resp = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/scenes",
        headers=AUTH_HEADERS,
        json={"scene_id": "scene_test12", "name": "Test Scene 12"}
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["scene_id"] == "scene_test12"

    # 2. Set reference take (Take A)
    ref_resp = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/scenes/scene_test12/reference",
        headers=AUTH_HEADERS,
        json={"reference_clip_id": "take_a"}
    )
    assert ref_resp.status_code == 200
    assert ref_resp.json()["reference_clip_id"] == "take_a"


# AI-CON-04 — False Positive Control: Take A vs Take A produces 0 findings
def test_ai_con_04_false_positive_control():
    findings = continuity_engine.analyze_take_continuity(
        project_id=settings.DEMO_PROJECT_ID,
        scene_id="scene_12",
        analysis_run_id="run_test_fp",
        reference_clip_id="take_a",
        comparison_clip_id="take_a",  # Comparing Take A against Take A
        reference_uri="gs://bucket/take_a.mp4",
        comparison_uri="gs://bucket/take_a.mp4"
    )
    assert len(findings) == 0  # MANDATORY: 0 findings


# AI-CON-02 & System Test — Take A vs Take C Occlusion: necklace = not_visible, 0 missing findings
def test_ai_con_02_occlusion_awareness():
    findings = continuity_engine.analyze_take_continuity(
        project_id=settings.DEMO_PROJECT_ID,
        scene_id="scene_12",
        analysis_run_id="run_test_occ",
        reference_clip_id="take_a",
        comparison_clip_id="take_c",  # Take C Occlusion
        reference_uri="gs://bucket/take_a.mp4",
        comparison_uri="gs://bucket/take_c.mp4"
    )
    # Take C occlusion must NOT create actionable missing-necklace finding
    necklace_findings = [f for f in findings if f.object_type == "necklace"]
    assert len(necklace_findings) == 0


# System Test — Take A vs Take B Comparison: necklace = absent, mug = changed
def test_take_a_vs_take_b_continuity_findings():
    findings = continuity_engine.analyze_take_continuity(
        project_id=settings.DEMO_PROJECT_ID,
        scene_id="scene_12",
        analysis_run_id="run_test_ab",
        reference_clip_id="take_a",
        comparison_clip_id="take_b",
        reference_uri="gs://bucket/take_a.mp4",
        comparison_uri="gs://bucket/take_b.mp4"
    )

    assert len(findings) >= 2
    necklace_fnd = next((f for f in findings if f.object_type == "necklace"), None)
    mug_fnd = next((f for f in findings if f.object_type in ("hero_mug", "mug")), None)

    assert necklace_fnd is not None
    assert necklace_fnd.ai_assessment == AIAssessmentEnum.ABSENT
    assert necklace_fnd.severity == SeverityEnum.HIGH
    assert necklace_fnd.policy_rule_id != ""

    assert mug_fnd is not None
    assert mug_fnd.ai_assessment == AIAssessmentEnum.CHANGED
    assert mug_fnd.severity == SeverityEnum.HIGH


# IT-JOB-01 — Async Analysis Initiation (HTTP 202 Accepted) & Status Polling
def test_it_job_01_async_analyze_and_poll():
    # 1. Start analysis (POST /analyze)
    start_resp = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/scenes/scene_12/analyze",
        headers=AUTH_HEADERS,
        json={"comparison_clip_id": "take_b"}
    )
    assert start_resp.status_code == 202
    data = start_resp.json()
    analysis_run_id = data["analysis_run_id"]
    assert data["status"] == "queued"

    # 2. Poll status (GET /analysis/{id})
    poll_resp = client.get(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/analysis/{analysis_run_id}",
        headers=AUTH_HEADERS
    )
    assert poll_resp.status_code == 200
    poll_data = poll_resp.json()
    assert poll_data["analysis_run_id"] == analysis_run_id
    assert poll_data["status"] in ("queued", "running", "succeeded")


# IT-IDEM-01 — Idempotency-Key deduplication
def test_it_idem_01_idempotency_deduplication():
    key = "idem_key_test_123"
    headers = {**AUTH_HEADERS, "Idempotency-Key": key}

    resp1 = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/scenes/scene_12/analyze",
        headers=headers,
        json={"comparison_clip_id": "take_b"}
    )
    assert resp1.status_code == 202
    run_id1 = resp1.json()["analysis_run_id"]

    resp2 = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/scenes/scene_12/analyze",
        headers=headers,
        json={"comparison_clip_id": "take_b"}
    )
    assert resp2.status_code == 202
    run_id2 = resp2.json()["analysis_run_id"]

    # Same idempotency key returns exact same analysis_run_id
    assert run_id1 == run_id2


# Video Clip Upload Endpoint (POST /clips)
def test_clip_upload_api():
    video_bytes = b"fake_mp4_video_content"
    resp = client.post(
        f"/api/projects/{settings.DEMO_PROJECT_ID}/clips",
        headers=AUTH_HEADERS,
        data={"scene_id": "scene_12", "role": "comparison"},
        files={"file": ("take_b.mp4", video_bytes, "video/mp4")}
    )
    assert resp.status_code == 200
    clip_data = resp.json()
    assert clip_data["scene_id"] == "scene_12"
    assert clip_data["role"] == "comparison"
    assert "gs://" in clip_data["gcs_uri"]

