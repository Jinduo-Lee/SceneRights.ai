from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.config import settings
from app.db.clickhouse import get_clickhouse_client, apply_migrations

router = APIRouter(prefix="/api/projects/{project_id}", tags=["seed"])


@router.post("/seed")
async def seed_project(project_id: str):
    """Demo-only endpoint: resets database tables and seeds demo project state."""
    if project_id != settings.DEMO_PROJECT_ID:
        raise HTTPException(status_code=400, detail="Invalid project_id for demo seed")

    client = get_clickhouse_client()

    # Apply DDL tables and view
    apply_migrations()

    # Clean existing rows for demo project_id
    tables = [
        "decisions",
        "findings",
        "analysis_runs",
        "policy_rules",
        "policy_documents",
        "clips",
        "scenes",
        "projects",
    ]
    for table in tables:
        client.command(f"ALTER TABLE {table} DELETE WHERE project_id = '{project_id}'")

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Seed Project
    client.command(
        f"INSERT INTO projects (project_id, name, status, created_at) "
        f"VALUES ('{project_id}', 'Scene 12 (Northstar Studios)', 'active', '{now_str}')"
    )

    # Seed Scene
    client.command(
        f"INSERT INTO scenes (project_id, scene_id, name, reference_clip_id, created_at) "
        f"VALUES ('{project_id}', 'scene_12', 'Scene 12', 'take_a', '{now_str}')"
    )

    # Seed Policy Document
    client.command(
        f"INSERT INTO policy_documents (project_id, policy_id, filename, gcs_uri, status, created_at, updated_at) "
        f"VALUES ('{project_id}', 'policy_001', 'northstar_scene12_policy.txt', 'gs://bucket/northstar_scene12_policy.txt', 'ready', '{now_str}', '{now_str}')"
    )

    # Seed Clips (Take A, Take B, Take C)
    client.command(
        f"INSERT INTO clips (project_id, clip_id, scene_id, role, gcs_uri, created_at) VALUES "
        f"('{project_id}', 'take_a', 'scene_12', 'reference', 'gs://bucket/take_a.mp4', '{now_str}'), "
        f"('{project_id}', 'take_b', 'scene_12', 'comparison', 'gs://bucket/take_b.mp4', '{now_str}'), "
        f"('{project_id}', 'take_c', 'scene_12', 'comparison', 'gs://bucket/take_c.mp4', '{now_str}')"
    )

    # Seed 3 Policy Rules (§7)
    client.command(
        f"INSERT INTO policy_rules (project_id, policy_id, policy_rule_id, document_name, policy_type, rule_text, source_quote, priority, status, version, created_at) VALUES "
        f"('{project_id}', 'policy_001', 'rule_001', 'northstar_scene12_policy.txt', 'continuity', 'Lead actor wears a silver necklace throughout Scene 12.', 'Lead actor wears a silver necklace throughout Scene 12.', 'high', 'approved', 1, '{now_str}'), "
        f"('{project_id}', 'policy_001', 'rule_002', 'northstar_scene12_policy.txt', 'continuity', 'Hero mug remains blue throughout Scene 12.', 'Hero mug remains blue throughout Scene 12.', 'high', 'approved', 1, '{now_str}'), "
        f"('{project_id}', 'policy_001', 'rule_003', 'northstar_scene12_policy.txt', 'visual_review', 'Flag visible unapproved fictional logos.', 'Flag visible unapproved fictional logos.', 'medium', 'approved', 1, '{now_str}')"
    )

    return {
        "status": "seeded",
        "project_id": project_id,
        "rules_count": 3,
        "clips_count": 3
    }

