import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def is_clickhouse_configured() -> bool:
    """Check if real ClickHouse credentials are configured in environment or .env."""
    return bool(settings.CLICKHOUSE_HOST and settings.CLICKHOUSE_HOST != "localhost")


@pytest.mark.skipif(
    not is_clickhouse_configured(),
    reason="ClickHouse Cloud credentials not configured in environment or .env (Section 20 CI Credential Safety)",
)
def test_seed_demo_project_flow():
    """Verify demo seed endpoint resets state and inserts 3 policy rules, clips, and scene."""
    project_id = settings.DEMO_PROJECT_ID
    response = client.post(f"/api/projects/{project_id}/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "seeded"
    assert data["project_id"] == project_id
    assert data["rules_count"] == 3
    assert data["clips_count"] == 3

