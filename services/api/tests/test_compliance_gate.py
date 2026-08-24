import sys
from pathlib import Path
import tempfile
import pytest

# Ensure repository root is on sys.path for importing scripts.compliance_gate
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.compliance_gate import (
    run_compliance_gate,
    check_python_dependencies,
    check_node_dependencies,
    check_executable_python_code,
    check_env_and_secrets,
)


@pytest.fixture
def temp_repo():
    """Creates a temporary workspace structure mimicking the repository."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create basic structure
        (tmp_path / "services" / "api").mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps" / "web").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)

        # Valid pyproject.toml
        (tmp_path / "services" / "api" / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["fastapi", "clickhouse-connect"]\n',
            encoding="utf-8",
        )

        # Valid package.json
        (tmp_path / "apps" / "web" / "package.json").write_text(
            '{"dependencies": {"next": "14.2.5", "react": "^18.3.1"}}',
            encoding="utf-8",
        )

        # Valid .gitignore
        (tmp_path / ".gitignore").write_text(".env\nnode_modules/\n.venv/\n", encoding="utf-8")

        # Valid .env.example
        (tmp_path / ".env.example").write_text(
            "CLICKHOUSE_HOST=localhost\nDEMO_ACCESS_TOKEN=demo-token\n",
            encoding="utf-8",
        )

        yield tmp_path


def test_comp_001_allowed_python_dependency(temp_repo):
    """TEST-COMP-001: Allowed Python dependency passes scanner."""
    violations = check_python_dependencies(temp_repo)
    assert len(violations) == 0


def test_comp_002_prohibited_ai_dependency(temp_repo):
    """TEST-COMP-002: Synthetic prohibited AI runtime dependency fails scanner."""
    pyproject = temp_repo / "services" / "api" / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\ndependencies = ["fastapi", "openai>=1.0.0"]\n',
        encoding="utf-8",
    )
    violations = check_python_dependencies(temp_repo)
    assert len(violations) == 1
    assert violations[0].rule_id == "AI-DEP-001"
    assert "openai" in violations[0].message


def test_comp_003_prohibited_agent_framework(temp_repo):
    """TEST-COMP-003: Synthetic prohibited agent-framework dependency fails scanner."""
    pyproject = temp_repo / "services" / "api" / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\ndependencies = ["langchain", "crewai"]\n',
        encoding="utf-8",
    )
    violations = check_python_dependencies(temp_repo)
    assert len(violations) == 2
    assert violations[0].rule_id == "AGENT-DEP-001"


def test_comp_004_prohibited_runtime_import(temp_repo):
    """TEST-COMP-004: Synthetic unauthorized AI import fails scanner."""
    bad_code = temp_repo / "services" / "api" / "bad_module.py"
    bad_code.write_text("import openai\nimport langchain\n", encoding="utf-8")

    violations = check_executable_python_code(temp_repo)
    assert len(violations) == 2
    assert any(v.rule_id == "AI-IMP-001" for v in violations)
    assert any(v.rule_id == "AGENT-DEP-001" for v in violations)


def test_comp_005_documentation_reference(temp_repo):
    """TEST-COMP-005: Mentioning a prohibited provider in documentation does not fail scanner."""
    doc_file = temp_repo / "docs" / "compliance.md"
    doc_file.write_text(
        "# Prohibited AI\nDo not use OpenAI, Anthropic, or LangChain.\n",
        encoding="utf-8",
    )
    # Executable code scan should not inspect docs/
    violations = check_executable_python_code(temp_repo)
    assert len(violations) == 0


def test_comp_006_opencv_dnn(temp_repo):
    """TEST-COMP-006: Synthetic executable usage of cv2.dnn fails scanner."""
    bad_cv = temp_repo / "tools" / "cv_helper.py"
    bad_cv.parent.mkdir(parents=True, exist_ok=True)
    bad_cv.write_text("import cv2\nmodel = cv2.dnn.readNet('model.caffemodel')\n", encoding="utf-8")

    violations = check_executable_python_code(temp_repo)
    assert len(violations) == 1
    assert violations[0].rule_id == "CV-001"
    assert "cv2.dnn" in violations[0].message


def test_comp_007_compliance_scanner_self_reference(temp_repo):
    """TEST-COMP-007: Compliance scanner's own definitions do not trigger false failure."""
    count, violations = run_compliance_gate(temp_repo)
    assert count == 0
    assert len(violations) == 0


def test_comp_008_gitignore_env_protection(temp_repo):
    """TEST-COMP-008: Gitignore protection for .env files is validated."""
    gitignore = temp_repo / ".gitignore"
    gitignore.write_text("node_modules/\n", encoding="utf-8")  # missing .env

    violations = check_env_and_secrets(temp_repo)
    assert len(violations) == 1
    assert violations[0].rule_id == "SECRET-001"


def test_comp_009_env_example_pass(temp_repo):
    """TEST-COMP-009: Safe placeholder .env.example passes scanner."""
    violations = check_env_and_secrets(temp_repo)
    assert len(violations) == 0


def test_comp_010_exit_status(temp_repo):
    """TEST-COMP-010: Compliant repo returns exit status 0, violating returns non-zero."""
    count, violations = run_compliance_gate(temp_repo)
    assert count == 0

    # Introduce synthetic violation
    (temp_repo / "services" / "api" / "violating.py").write_text("import anthropic\n", encoding="utf-8")
    count, violations = run_compliance_gate(temp_repo)
    assert count == 1
