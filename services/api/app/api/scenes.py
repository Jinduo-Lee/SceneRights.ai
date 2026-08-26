from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.config import settings
from app.api.deps import verify_demo_access_token, raise_api_error
from app.db.clickhouse import get_clickhouse_client
from app.schemas.enums import (
    ErrorCodeEnum,
    FindingTypeEnum,
    AIAssessmentEnum,
    ModelAssessmentEnum,
    SeverityEnum,
    ReviewStatusEnum,
)
from app.schemas.scene import Scene
from app.schemas.finding import Finding

router = APIRouter(prefix="/api/projects/{project_id}", tags=["scenes"])


class CreateSceneRequest(BaseModel):
    scene_id: str = "scene_12"
    name: str = "Scene 12"


class SetReferenceRequest(BaseModel):
    reference_clip_id: str


@router.post("/scenes", response_model=Scene)
async def create_scene(
    project_id: str,
    body: CreateSceneRequest,
    token: str = Depends(verify_demo_access_token)
):
    """Creates a new continuity scene."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    client = get_clickhouse_client()

    # Clean existing scene if re-created
    client.command(f"ALTER TABLE scenes DELETE WHERE project_id = '{project_id}' AND scene_id = '{body.scene_id}'")

    client.command(
        f"INSERT INTO scenes (project_id, scene_id, name, reference_clip_id, created_at) "
        f"VALUES ('{project_id}', '{body.scene_id}', '{body.name}', '', '{now_str}')"
    )

    return Scene(
        project_id=project_id,
        scene_id=body.scene_id,
        name=body.name,
        reference_clip_id=None,
        created_at=now
    )


@router.get("/scenes/{scene_id}", response_model=Scene)
async def get_scene(
    project_id: str,
    scene_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Fetches details for a continuity scene."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, scene_id, name, reference_clip_id, created_at "
        f"FROM scenes WHERE project_id = '{project_id}' AND scene_id = '{scene_id}'"
    )

    if not query_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Scene '{scene_id}' not found."
        )

    row = query_res.result_rows[0]
    return Scene(
        project_id=row[0],
        scene_id=row[1],
        name=row[2],
        reference_clip_id=row[3] if row[3] else None,
        created_at=row[4]
    )


@router.post("/scenes/{scene_id}/reference", response_model=Scene)
async def set_scene_reference(
    project_id: str,
    scene_id: str,
    body: SetReferenceRequest,
    token: str = Depends(verify_demo_access_token)
):
    """Sets the reference take for a continuity scene."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()

    # Verify clip exists for this project
    clip_res = client.query(
        f"SELECT clip_id FROM clips WHERE project_id = '{project_id}' AND clip_id = '{body.reference_clip_id}'"
    )
    if not clip_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Reference clip '{body.reference_clip_id}' not found under project '{project_id}'."
        )

    # Fetch existing scene name & created_at
    scene_res = client.query(
        f"SELECT name, created_at FROM scenes WHERE project_id = '{project_id}' AND scene_id = '{scene_id}'"
    )
    scene_name = scene_res.result_rows[0][0] if scene_res.result_rows else "Scene 12"
    created_at = scene_res.result_rows[0][1] if scene_res.result_rows else datetime.now()
    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at)

    # Re-insert scenes row to guarantee immediate synchronous update without mutation delay
    client.command(f"ALTER TABLE scenes DELETE WHERE project_id = '{project_id}' AND scene_id = '{scene_id}'")
    client.command(
        f"INSERT INTO scenes (project_id, scene_id, name, reference_clip_id, created_at) "
        f"VALUES ('{project_id}', '{scene_id}', '{scene_name}', '{body.reference_clip_id}', '{created_at_str}')"
    )

    return Scene(
        project_id=project_id,
        scene_id=scene_id,
        name=scene_name,
        reference_clip_id=body.reference_clip_id,
        created_at=created_at if isinstance(created_at, datetime) else datetime.now()
    )


@router.get("/scenes/{scene_id}/findings", response_model=List[Finding])
async def get_scene_findings(
    project_id: str,
    scene_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Fetches all continuity findings for a scene, joined with findings_current review status."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()

    query_res = client.query(
        f"SELECT f.project_id, f.scene_id, f.finding_id, f.analysis_run_id, f.finding_type, "
        f"f.object_type, f.object_label, f.reference_clip, f.comparison_clip, f.ai_assessment, "
        f"f.model_assessment, f.severity, f.policy_rule_id, f.policy_rule_version, f.policy_document, "
        f"f.policy_rule, f.source_quote, f.timestamp_ms, f.created_at, coalesce(nullIf(d.review_status, ''), 'open') AS review_status "
        f"FROM findings AS f "
        f"LEFT JOIN ("
        f"  SELECT project_id, finding_id, argMax(review_status, created_at) AS review_status "
        f"  FROM decisions GROUP BY project_id, finding_id"
        f") AS d ON f.project_id = d.project_id AND f.finding_id = d.finding_id "
        f"WHERE f.project_id = '{project_id}' AND f.scene_id = '{scene_id}' "
        f"ORDER BY f.created_at ASC"
    )

    findings = []
    for row in query_res.result_rows:
        findings.append(
            Finding(
                project_id=row[0],
                scene_id=row[1],
                finding_id=row[2],
                analysis_run_id=row[3],
                finding_type=FindingTypeEnum(row[4]),
                object_type=row[5],
                object_label=row[6],
                reference_clip=row[7],
                comparison_clip=row[8],
                ai_assessment=AIAssessmentEnum(row[9]),
                model_assessment=ModelAssessmentEnum(row[10]),
                severity=SeverityEnum(row[11]),
                policy_rule_id=row[12],
                policy_rule_version=row[13],
                policy_document=row[14],
                policy_rule=row[15],
                source_quote=row[16],
                timestamp_ms=row[17],
                created_at=row[18],
                review_status=ReviewStatusEnum(row[19])
            )
        )
    return findings

