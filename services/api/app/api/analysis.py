import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Header, BackgroundTasks, Depends, status
from pydantic import BaseModel
from app.config import settings
from app.api.deps import verify_demo_access_token, raise_api_error
from app.db.clickhouse import get_clickhouse_client
from app.schemas.enums import AnalysisRunStatusEnum, ErrorCodeEnum
from app.schemas.analysis import AnalysisRun
from app.schemas.continuity_dto import AnalyzeResponse
from app.services.continuity import continuity_engine

router = APIRouter(prefix="/api/projects/{project_id}", tags=["analysis"])

# In-memory idempotency cache for active session runs
IDEMPOTENCY_CACHE = {}


class StartAnalysisRequest(BaseModel):
    comparison_clip_id: str = "take_b"


def execute_async_analysis_task(
    project_id: str,
    scene_id: str,
    analysis_run_id: str,
    reference_clip_id: str,
    comparison_clip_id: str
):
    """Background worker function executing the Milestone 3 continuity analysis pipeline."""
    client = get_clickhouse_client()

    try:
        # Update step -> extracting_frames
        client.command(
            f"ALTER TABLE analysis_runs UPDATE status = 'running', step = 'extracting_frames' "
            f"WHERE project_id = '{project_id}' AND scene_id = '{scene_id}' AND analysis_run_id = '{analysis_run_id}'"
        )

        # Get clips URIs
        ref_res = client.query(
            f"SELECT gcs_uri FROM clips WHERE project_id = '{project_id}' AND clip_id = '{reference_clip_id}'"
        )
        comp_res = client.query(
            f"SELECT gcs_uri FROM clips WHERE project_id = '{project_id}' AND clip_id = '{comparison_clip_id}'"
        )

        ref_uri = ref_res.result_rows[0][0] if ref_res.result_rows else f"gs://{settings.GCS_BUCKET}/take_a.mp4"
        comp_uri = comp_res.result_rows[0][0] if comp_res.result_rows else f"gs://{settings.GCS_BUCKET}/{comparison_clip_id}.mp4"

        # Update step -> comparing_frames
        client.command(
            f"ALTER TABLE analysis_runs UPDATE step = 'comparing_frames' "
            f"WHERE project_id = '{project_id}' AND scene_id = '{scene_id}' AND analysis_run_id = '{analysis_run_id}'"
        )

        # Run continuity comparison and finding generation
        created_findings = continuity_engine.analyze_take_continuity(
            project_id=project_id,
            scene_id=scene_id,
            analysis_run_id=analysis_run_id,
            reference_clip_id=reference_clip_id,
            comparison_clip_id=comparison_clip_id,
            reference_uri=ref_uri,
            comparison_uri=comp_uri,
            reference_filename=f"{reference_clip_id}.mp4",
            comparison_filename=f"{comparison_clip_id}.mp4"
        )

        # Update step -> completed & status -> succeeded
        completed_now = datetime.now()
        completed_str = completed_now.strftime("%Y-%m-%d %H:%M:%S")

        client.command(
            f"ALTER TABLE analysis_runs UPDATE status = 'succeeded', step = 'completed', completed_at = '{completed_str}' "
            f"WHERE project_id = '{project_id}' AND scene_id = '{scene_id}' AND analysis_run_id = '{analysis_run_id}'"
        )

    except Exception as e:
        completed_now = datetime.now()
        completed_str = completed_now.strftime("%Y-%m-%d %H:%M:%S")
        client.command(
            f"ALTER TABLE analysis_runs UPDATE status = 'failed', step = 'failed', error_code = 'MEDIA_PROCESSING_FAILED', completed_at = '{completed_str}' "
            f"WHERE project_id = '{project_id}' AND scene_id = '{scene_id}' AND analysis_run_id = '{analysis_run_id}'"
        )


@router.post("/scenes/{scene_id}/analyze", status_code=status.HTTP_202_ACCEPTED, response_model=AnalyzeResponse)
async def start_scene_analysis(
    project_id: str,
    scene_id: str,
    body: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    token: str = Depends(verify_demo_access_token)
):
    """Initiates asynchronous continuity analysis for a scene (HTTP 202 Accepted). Supports Idempotency-Key."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()

    # Query reference clip for scene
    scene_res = client.query(
        f"SELECT reference_clip_id FROM scenes WHERE project_id = '{project_id}' AND scene_id = '{scene_id}'"
    )
    reference_clip_id = scene_res.result_rows[0][0] if scene_res.result_rows and scene_res.result_rows[0][0] else "take_a"
    comparison_clip_id = body.comparison_clip_id

    # Check Idempotency-Key header to prevent duplicate runs
    if idempotency_key:
        if idempotency_key in IDEMPOTENCY_CACHE:
            existing_run_id = IDEMPOTENCY_CACHE[idempotency_key]
            return AnalyzeResponse(analysis_run_id=existing_run_id, status="queued")

    analysis_run_id = f"run_{uuid.uuid4().hex[:8]}"
    if idempotency_key:
        IDEMPOTENCY_CACHE[idempotency_key] = analysis_run_id

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Persist initial analysis_runs record
    client.command(
        f"INSERT INTO analysis_runs (project_id, scene_id, analysis_run_id, status, step, started_at) "
        f"VALUES ('{project_id}', '{scene_id}', '{analysis_run_id}', 'queued', 'queued', '{now_str}')"
    )

    # Launch background worker
    background_tasks.add_task(
        execute_async_analysis_task,
        project_id,
        scene_id,
        analysis_run_id,
        reference_clip_id,
        comparison_clip_id
    )

    return AnalyzeResponse(
        analysis_run_id=analysis_run_id,
        status="queued"
    )


@router.get("/analysis/{analysis_run_id}", response_model=AnalysisRun)
async def get_analysis_run_status(
    project_id: str,
    analysis_run_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Polls async analysis run status from ClickHouse analysis_runs table."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, scene_id, analysis_run_id, status, step, error_code, started_at, completed_at "
        f"FROM analysis_runs WHERE project_id = '{project_id}' AND analysis_run_id = '{analysis_run_id}'"
    )

    if not query_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Analysis run '{analysis_run_id}' not found."
        )

    row = query_res.result_rows[0]

    # Count findings for this analysis run
    fnd_res = client.query(
        f"SELECT count() FROM findings WHERE project_id = '{project_id}' AND analysis_run_id = '{analysis_run_id}'"
    )
    findings_count = fnd_res.result_rows[0][0] if fnd_res.result_rows else 0

    return AnalysisRun(
        project_id=row[0],
        scene_id=row[1],
        analysis_run_id=row[2],
        status=AnalysisRunStatusEnum(row[3]),
        step=row[4],
        error_code=row[5] if row[5] else None,
        started_at=row[6],
        completed_at=row[7] if row[7] else None,
        findings_count=findings_count
    )

