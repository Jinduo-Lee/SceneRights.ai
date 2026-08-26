import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, status
from app.config import settings
from app.api.deps import verify_demo_access_token, raise_api_error
from app.db.clickhouse import get_clickhouse_client
from app.schemas.enums import ClipRoleEnum, ErrorCodeEnum
from app.schemas.scene import Clip
from app.services.storage import storage_service, sanitize_filename
from app.services.video_processor import validate_video_file

router = APIRouter(prefix="/api/projects/{project_id}", tags=["clips"])


@router.post("/clips", response_model=Clip)
async def upload_clip(
    project_id: str,
    file: UploadFile = File(...),
    scene_id: str = Form("scene_12"),
    role: str = Form("comparison"),
    token: str = Depends(verify_demo_access_token)
):
    """Uploads a video clip to private GCS and creates a clips record."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    content = await file.read()
    filename = file.filename or "take.mp4"

    # Validate file size (<100MB) and format
    valid, err_msg = validate_video_file(filename, len(content))
    if not valid:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=err_msg
        )

    clip_id = f"clip_{uuid.uuid4().hex[:8]}"
    safe_name = sanitize_filename(filename)
    object_path = f"projects/{project_id}/clips/{clip_id}/{safe_name}"
    gcs_uri = f"gs://{storage_service.bucket_name}/{object_path}"

    try:
        # Upload media file privately to storage
        storage_service.upload_policy_document(project_id, clip_id, filename, content)
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=f"Failed to store video media object: {str(e)}"
        )

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Determine clip role enum
    role_enum = ClipRoleEnum.REFERENCE if role.lower() == "reference" else ClipRoleEnum.COMPARISON

    client = get_clickhouse_client()
    try:
        client.command(
            f"INSERT INTO clips (project_id, clip_id, scene_id, role, gcs_uri, created_at) "
            f"VALUES ('{project_id}', '{clip_id}', '{scene_id}', '{role_enum.value}', '{gcs_uri}', '{now_str}')"
        )
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=f"Database error persisting clip metadata: {str(e)}"
        )

    return Clip(
        project_id=project_id,
        clip_id=clip_id,
        scene_id=scene_id,
        role=role_enum,
        gcs_uri=gcs_uri,
        created_at=now
    )


@router.get("/clips", response_model=List[Clip])
async def list_clips(
    project_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Lists video clips for project."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, clip_id, scene_id, role, gcs_uri, created_at "
        f"FROM clips WHERE project_id = '{project_id}' ORDER BY created_at DESC"
    )

    clips = []
    for row in query_res.result_rows:
        clips.append(
            Clip(
                project_id=row[0],
                clip_id=row[1],
                scene_id=row[2],
                role=ClipRoleEnum(row[3]),
                gcs_uri=row[4],
                created_at=row[5]
            )
        )
    return clips

