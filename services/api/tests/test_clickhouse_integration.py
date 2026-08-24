from datetime import datetime
import pytest
from app.config import settings
from app.db.clickhouse import get_clickhouse_client, apply_migrations


def test_clickhouse_config_loading():
    """Verify ClickHouse configuration loads without exposing secrets."""
    assert settings.CLICKHOUSE_HOST != ""
    assert settings.CLICKHOUSE_PORT > 0
    assert settings.CLICKHOUSE_USER != ""
    assert settings.CLICKHOUSE_DATABASE != ""


def test_clickhouse_cloud_connectivity_and_migrations():
    """Test connectivity to ClickHouse Cloud and apply authoritative DDL."""
    client = get_clickhouse_client()

    # Simple ping / SELECT 1
    res = client.command("SELECT 1")
    assert res == 1

    # Apply DDL
    applied_files = apply_migrations()
    assert len(applied_files) >= 9

    # Verify tables exist
    tables_res = client.query("SHOW TABLES").result_rows
    table_names = [r[0] for r in tables_res]

    expected_entities = [
        "projects",
        "policy_documents",
        "clips",
        "scenes",
        "policy_rules",
        "analysis_runs",
        "findings",
        "decisions",
        "agent_runs",
        "findings_current",
    ]

    for entity in expected_entities:
        assert entity in table_names, f"Missing entity {entity} in ClickHouse Cloud"


def test_append_only_finding_and_decision_lifecycle():
    """Verify append-only findings + decisions state derivation in findings_current."""
    client = get_clickhouse_client()
    project_id = settings.DEMO_PROJECT_ID
    scene_id = "scene_12"
    finding_id = "test_find_101"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean previous test row if exists
    client.command(f"ALTER TABLE findings DELETE WHERE finding_id = '{finding_id}'")
    client.command(f"ALTER TABLE decisions DELETE WHERE finding_id = '{finding_id}'")

    # Step 6: INSERT into findings
    client.command(
        f"INSERT INTO findings (project_id, scene_id, finding_id, analysis_run_id, finding_type, "
        f"object_type, object_label, reference_clip, comparison_clip, ai_assessment, model_assessment, "
        f"severity, policy_rule_id, policy_rule_version, policy_document, policy_rule, source_quote, timestamp_ms, created_at) "
        f"VALUES ('{project_id}', '{scene_id}', '{finding_id}', 'run_001', 'continuity', "
        f"'necklace', 'lead actor silver necklace', 'take_a', 'take_b', 'absent', 'clear', "
        f"'high', 'rule_001', 1, 'northstar_scene12_policy.txt', 'Lead actor wears silver necklace', "
        f"'Lead actor wears silver necklace', 5000, '{now_str}')"
    )

    # Verify findings_current initially shows review_status = 'open' via coalesce
    curr_initial = client.query(
        f"SELECT review_status FROM findings_current WHERE project_id = '{project_id}' AND finding_id = '{finding_id}'"
    ).result_rows
    assert len(curr_initial) == 1
    assert curr_initial[0][0] == "open"

    # Step 7: INSERT a decision for that finding
    client.command(
        f"INSERT INTO decisions (project_id, finding_id, review_status, previous_status, reviewer, comment, created_at) "
        f"VALUES ('{project_id}', '{finding_id}', 'confirmed', 'open', 'reviewer_alice', 'Confirmed necklace is missing', '{now_str}')"
    )

    # Step 8: Query findings_current and verify latest review_status is reflected
    curr_after = client.query(
        f"SELECT review_status, last_reviewer FROM findings_current WHERE project_id = '{project_id}' AND finding_id = '{finding_id}'"
    ).result_rows
    assert len(curr_after) == 1
    assert curr_after[0][0] == "confirmed"
    assert curr_after[0][1] == "reviewer_alice"

    # Insert second decision resolving finding
    client.command(
        f"INSERT INTO decisions (project_id, finding_id, review_status, previous_status, reviewer, comment, created_at) "
        f"VALUES ('{project_id}', '{finding_id}', 'resolved', 'confirmed', 'reviewer_bob', 'Reshoot approved', '{now_str}')"
    )

    curr_resolved = client.query(
        f"SELECT review_status, last_reviewer FROM findings_current WHERE project_id = '{project_id}' AND finding_id = '{finding_id}'"
    ).result_rows
    assert len(curr_resolved) == 1
    assert curr_resolved[0][0] == "resolved"
    assert curr_resolved[0][1] == "reviewer_bob"

    # Step 9: Verify original finding in findings table remains unchanged
    orig = client.query(
        f"SELECT ai_assessment, severity FROM findings WHERE finding_id = '{finding_id}'"
    ).result_rows
    assert len(orig) == 1
    assert orig[0][0] == "absent"
    assert orig[0][1] == "high"

    # Step 10: Verify project_id scoping
    scoped_other = client.query(
        f"SELECT * FROM findings_current WHERE project_id = 'other_project_999' AND finding_id = '{finding_id}'"
    ).result_rows
    assert len(scoped_other) == 0

    # Cleanup test row
    client.command(f"ALTER TABLE findings DELETE WHERE finding_id = '{finding_id}'")
    client.command(f"ALTER TABLE decisions DELETE WHERE finding_id = '{finding_id}'")

