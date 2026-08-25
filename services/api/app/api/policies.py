import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.config import settings
from app.api.deps import verify_demo_access_token, raise_api_error
from app.db.clickhouse import get_clickhouse_client
from app.schemas.enums import (
    PolicyDocumentStatusEnum,
    PolicyRuleStatusEnum,
    PriorityEnum,
    ErrorCodeEnum,
)
from app.schemas.policy import (
    PolicyDocument,
    PolicyRule,
    PolicyProcessResponse,
)
from app.services.storage import storage_service
from app.services.policy_parser import parse_policy_document, validate_policy_file
from app.services.policy_extractor import policy_extractor, validate_exact_source_quote

router = APIRouter(prefix="/api/projects/{project_id}", tags=["policies"])


@router.post("/policies", response_model=PolicyDocument)
async def upload_policy(
    project_id: str,
    file: UploadFile = File(...),
    token: str = Depends(verify_demo_access_token)
):
    """Uploads a policy document to private GCS and creates policy_documents record."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    content = await file.read()
    filename = file.filename or "policy_document.txt"

    # Server-side validation
    valid, err_msg = validate_policy_file(filename, len(content))
    if not valid:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=err_msg
        )

    policy_id = f"policy_{uuid.uuid4().hex[:8]}"
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Upload to private GCS storage
    try:
        gcs_uri = storage_service.upload_policy_document(project_id, policy_id, filename, content)
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=f"Failed to upload document to storage: {str(e)}"
        )

    # ClickHouse persistence
    client = get_clickhouse_client()
    try:
        client.command(
            f"INSERT INTO policy_documents (project_id, policy_id, filename, gcs_uri, status, created_at, updated_at) "
            f"VALUES ('{project_id}', '{policy_id}', '{filename}', '{gcs_uri}', '{PolicyDocumentStatusEnum.UPLOADED.value}', '{now_str}', '{now_str}')"
        )
    except Exception as e:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.UPLOAD_FAILED,
            message=f"Database error persisting policy document: {str(e)}"
        )

    return PolicyDocument(
        project_id=project_id,
        policy_id=policy_id,
        filename=filename,
        gcs_uri=gcs_uri,
        status=PolicyDocumentStatusEnum.UPLOADED,
        created_at=now,
        updated_at=now
    )


@router.post("/policies/{policy_id}/process", response_model=PolicyProcessResponse)
async def process_policy(
    project_id: str,
    policy_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Processes uploaded policy document: text parsing -> Gemini rule extraction -> exact quote validation -> persistence."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()

    # Query policy metadata
    query_res = client.query(
        f"SELECT filename, gcs_uri, status FROM policy_documents WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
    )
    if not query_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Policy document '{policy_id}' not found."
        )

    filename, gcs_uri, _ = query_res.result_rows[0]
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Update status to processing
    client.command(
        f"ALTER TABLE policy_documents UPDATE status = '{PolicyDocumentStatusEnum.PROCESSING.value}', updated_at = '{now_str}' "
        f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
    )

    try:
        # Download and parse document text
        content = storage_service.download_policy_document(gcs_uri)
        parsed_text = parse_policy_document(filename, content)
    except ValueError as ve:
        client.command(
            f"ALTER TABLE policy_documents UPDATE status = '{PolicyDocumentStatusEnum.FAILED.value}', updated_at = '{now_str}' "
            f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
        )
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.PARSE_FAILED,
            message=str(ve)
        )
    except Exception as e:
        client.command(
            f"ALTER TABLE policy_documents UPDATE status = '{PolicyDocumentStatusEnum.FAILED.value}', updated_at = '{now_str}' "
            f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
        )
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.PARSE_FAILED,
            message=f"Error retrieving policy document content: {str(e)}"
        )

    # Gemini extraction
    try:
        extracted_candidates = policy_extractor.extract_candidate_rules(parsed_text)
    except Exception as e:
        client.command(
            f"ALTER TABLE policy_documents UPDATE status = '{PolicyDocumentStatusEnum.FAILED.value}', updated_at = '{now_str}' "
            f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
        )
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCodeEnum.INVALID_GEMINI_OUTPUT,
            message=f"Gemini rule extraction failed: {str(e)}"
        )

    saved_rules: List[PolicyRule] = []

    # Grounding validation & persistence
    for idx, candidate in enumerate(extracted_candidates, start=1):
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        is_grounded = validate_exact_source_quote(candidate.source_quote, parsed_text)

        # Grounded rules become 'extracted'; ungrounded rules are auto-rejected
        rule_status = PolicyRuleStatusEnum.EXTRACTED if is_grounded else PolicyRuleStatusEnum.REJECTED

        # Sanitize single quotes for SQL insertion
        clean_text = candidate.rule_text.replace("'", "''")
        clean_quote = candidate.source_quote.replace("'", "''")
        clean_doc_name = filename.replace("'", "''")

        client.command(
            f"INSERT INTO policy_rules (project_id, policy_id, policy_rule_id, document_name, policy_type, rule_text, source_quote, priority, status, version, created_at) "
            f"VALUES ('{project_id}', '{policy_id}', '{rule_id}', '{clean_doc_name}', '{candidate.category}', '{clean_text}', '{clean_quote}', '{candidate.priority.value}', '{rule_status.value}', 1, '{now_str}')"
        )

        saved_rules.append(
            PolicyRule(
                project_id=project_id,
                policy_id=policy_id,
                policy_rule_id=rule_id,
                document_name=filename,
                policy_type=candidate.category,
                rule_text=candidate.rule_text,
                source_quote=candidate.source_quote,
                priority=candidate.priority,
                status=rule_status,
                version=1,
                created_at=now
            )
        )

    # Mark document as ready
    client.command(
        f"ALTER TABLE policy_documents UPDATE status = '{PolicyDocumentStatusEnum.READY.value}', updated_at = '{now_str}' "
        f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
    )

    return PolicyProcessResponse(
        policy_id=policy_id,
        status=PolicyDocumentStatusEnum.READY,
        rules_extracted=len(saved_rules),
        rules=saved_rules
    )


@router.get("/policies", response_model=List[PolicyDocument])
async def list_policies(
    project_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Lists policy documents for project."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, policy_id, filename, gcs_uri, status, created_at, updated_at "
        f"FROM policy_documents WHERE project_id = '{project_id}' ORDER BY created_at DESC"
    )

    docs = []
    for row in query_res.result_rows:
        docs.append(
            PolicyDocument(
                project_id=row[0],
                policy_id=row[1],
                filename=row[2],
                gcs_uri=row[3],
                status=PolicyDocumentStatusEnum(row[4]),
                created_at=row[5],
                updated_at=row[6]
            )
        )
    return docs


@router.get("/policies/{policy_id}/rules", response_model=List[PolicyRule])
async def list_policy_rules(
    project_id: str,
    policy_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Lists policy rules for specified policy document."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, policy_id, policy_rule_id, document_name, policy_type, rule_text, source_quote, priority, status, version, effective_date, created_at "
        f"FROM policy_rules WHERE project_id = '{project_id}' AND policy_id = '{policy_id}' ORDER BY created_at ASC"
    )

    rules = []
    for row in query_res.result_rows:
        rules.append(
            PolicyRule(
                project_id=row[0],
                policy_id=row[1],
                policy_rule_id=row[2],
                document_name=row[3],
                policy_type=row[4],
                rule_text=row[5],
                source_quote=row[6],
                priority=PriorityEnum(row[7]),
                status=PolicyRuleStatusEnum(row[8]),
                version=row[9],
                effective_date=row[10],
                created_at=row[11]
            )
        )
    return rules


@router.post("/policies/{policy_id}/rules/{policy_rule_id}/approve", response_model=PolicyRule)
async def approve_policy_rule(
    project_id: str,
    policy_id: str,
    policy_rule_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Human approval of extracted policy rule. Ungrounded/auto-rejected rules cannot be approved."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, policy_id, policy_rule_id, document_name, policy_type, rule_text, source_quote, priority, status, version, effective_date, created_at "
        f"FROM policy_rules WHERE project_id = '{project_id}' AND policy_id = '{policy_id}' AND policy_rule_id = '{policy_rule_id}'"
    )

    if not query_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Policy rule '{policy_rule_id}' not found under policy '{policy_id}'."
        )

    row = query_res.result_rows[0]
    source_quote = row[6]
    gcs_uri_res = client.query(
        f"SELECT gcs_uri, filename FROM policy_documents WHERE project_id = '{project_id}' AND policy_id = '{policy_id}'"
    )

    # Double-check grounding invariant before approving
    if gcs_uri_res.result_rows:
        gcs_uri, filename = gcs_uri_res.result_rows[0]
        try:
            content = storage_service.download_policy_document(gcs_uri)
            parsed_text = parse_policy_document(filename, content)
            if not validate_exact_source_quote(source_quote, parsed_text):
                raise_api_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code=ErrorCodeEnum.INVALID_TRANSITION,
                    message="Cannot approve ungrounded rule whose source quote fails exact substring validation."
                )
        except HTTPException:
            raise
        except Exception:
            pass

    client.command(
        f"ALTER TABLE policy_rules UPDATE status = '{PolicyRuleStatusEnum.APPROVED.value}' "
        f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}' AND policy_rule_id = '{policy_rule_id}'"
    )

    return PolicyRule(
        project_id=row[0],
        policy_id=row[1],
        policy_rule_id=row[2],
        document_name=row[3],
        policy_type=row[4],
        rule_text=row[5],
        source_quote=row[6],
        priority=PriorityEnum(row[7]),
        status=PolicyRuleStatusEnum.APPROVED,
        version=row[9],
        effective_date=row[10],
        created_at=row[11]
    )


@router.post("/policies/{policy_id}/rules/{policy_rule_id}/reject", response_model=PolicyRule)
async def reject_policy_rule(
    project_id: str,
    policy_id: str,
    policy_rule_id: str,
    token: str = Depends(verify_demo_access_token)
):
    """Human rejection of extracted policy rule."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message=f"Access denied for project '{project_id}'."
        )

    client = get_clickhouse_client()
    query_res = client.query(
        f"SELECT project_id, policy_id, policy_rule_id, document_name, policy_type, rule_text, source_quote, priority, status, version, effective_date, created_at "
        f"FROM policy_rules WHERE project_id = '{project_id}' AND policy_id = '{policy_id}' AND policy_rule_id = '{policy_rule_id}'"
    )

    if not query_res.result_rows:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodeEnum.NOT_FOUND,
            message=f"Policy rule '{policy_rule_id}' not found under policy '{policy_id}'."
        )

    row = query_res.result_rows[0]

    client.command(
        f"ALTER TABLE policy_rules UPDATE status = '{PolicyRuleStatusEnum.REJECTED.value}' "
        f"WHERE project_id = '{project_id}' AND policy_id = '{policy_id}' AND policy_rule_id = '{policy_rule_id}'"
    )

    return PolicyRule(
        project_id=row[0],
        policy_id=row[1],
        policy_rule_id=row[2],
        document_name=row[3],
        policy_type=row[4],
        rule_text=row[5],
        source_quote=row[6],
        priority=PriorityEnum(row[7]),
        status=PolicyRuleStatusEnum.REJECTED,
        version=row[9],
        effective_date=row[10],
        created_at=row[11]
    )

