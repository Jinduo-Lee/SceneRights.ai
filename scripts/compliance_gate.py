#!/usr/bin/env python3
"""SceneRights AI Compliance Gate Script (Milestone 1D / Milestone 3).

Enforces repository compliance rules per SceneRights AI v6.2.2 Master Spec
and Milestone 1D/3 Compliance Baseline Specification.
"""

import ast
import json
import re
import sys
from pathlib import Path

# Base directory (repository root)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Allowed Python runtime and dev dependencies
ALLOWED_PYTHON_DEPENDENCIES = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings",
    "clickhouse-connect",
    "google-genai",
    "google-adk",
    "google-cloud-storage",
    "opencv-python-headless",
    "opencv-python",
    "pypdf",
    "python-docx",
    "python-multipart",
    "imageio-ffmpeg",
    "ffmpeg-python",
    "pytest",
    "pytest-asyncio",
    "httpx",
    "setuptools",
    "wheel",
    "pip",
    "anyio",
    "starlette",
}

# Prohibited Python packages (AI providers & agent frameworks)
PROHIBITED_PYTHON_PACKAGES = {
    "openai",
    "anthropic",
    "cohere",
    "mistralai",
    "groq",
    "together",
    "huggingface_hub",
    "transformers",
    "langchain",
    "langchain-core",
    "langchain-community",
    "langgraph",
    "crewai",
    "autogen",
    "pyautogen",
    "semantic-kernel",
}

# Allowed Node.js dependencies
ALLOWED_NODE_DEPENDENCIES = {
    "next",
    "react",
    "react-dom",
    "typescript",
    "@types/react",
    "@types/react-dom",
    "@types/node",
    "tailwindcss",
    "autoprefixer",
    "postcss",
    "clsx",
    "tailwind-merge",
    "lucide-react",
}

# Prohibited Node.js packages
PROHIBITED_NODE_PACKAGES = {
    "openai",
    "@anthropic-ai/sdk",
    "cohere-ai",
    "langchain",
    "@langchain/core",
    "@langchain/community",
    "@langchain/openai",
    "@langchain/anthropic",
    "crewai",
    "autogen",
}

# Directories to scan for executable source code
EXECUTABLE_DIRS = ["services", "agents", "tools", "apps"]

# Prohibited OpenCV symbols
PROHIBITED_OPENCV_SYMBOLS = ["cv2.dnn", "cv2.CascadeClassifier", "cv2.face"]

# Prohibited import modules in Python
PROHIBITED_PYTHON_IMPORTS = {
    "openai": "AI-IMP-001",
    "anthropic": "AI-IMP-001",
    "cohere": "AI-IMP-001",
    "mistralai": "AI-IMP-001",
    "groq": "AI-IMP-001",
    "together": "AI-IMP-001",
    "transformers": "AI-IMP-001",
    "langchain": "AGENT-DEP-001",
    "langgraph": "AGENT-DEP-001",
    "crewai": "AGENT-DEP-001",
    "autogen": "AGENT-DEP-001",
    "semantic_kernel": "AGENT-DEP-001",
}


class ComplianceViolation:
    def __init__(self, rule_id: str, file_path: str, message: str):
        self.rule_id = rule_id
        self.file_path = file_path
        self.message = message

    def __str__(self):
        return f"FAIL [{self.rule_id}]: {self.message} (file: {self.file_path})"


def check_python_dependencies(root_dir: Path) -> list[ComplianceViolation]:
    violations = []
    pyproject_path = root_dir / "services" / "api" / "pyproject.toml"
    if not pyproject_path.exists():
        return violations

    content = pyproject_path.read_text(encoding="utf-8")
    
    # Parse dependencies section
    dep_matches = re.findall(r'"([a-zA-Z0-9_\-\[\]]+)(?:[>=<~!^].*)?"', content)
    for raw_dep in dep_matches:
        base_dep = raw_dep.split("[")[0].lower()
        if base_dep in PROHIBITED_PYTHON_PACKAGES:
            rule_id = "AGENT-DEP-001" if "lang" in base_dep or "crew" in base_dep or "autogen" in base_dep else "AI-DEP-001"
            violations.append(
                ComplianceViolation(
                    rule_id,
                    str(pyproject_path.relative_to(root_dir)),
                    f"Unauthorized Python runtime dependency detected: '{base_dep}'",
                )
            )
    return violations


def check_node_dependencies(root_dir: Path) -> list[ComplianceViolation]:
    violations = []
    package_json_path = root_dir / "apps" / "web" / "package.json"
    if not package_json_path.exists():
        return violations

    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except Exception:
        return violations

    all_deps = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))

    for pkg_name in all_deps:
        pkg_lower = pkg_name.lower()
        if pkg_lower in PROHIBITED_NODE_PACKAGES:
            rule_id = "AGENT-DEP-001" if "langchain" in pkg_lower or "crewai" in pkg_lower or "autogen" in pkg_lower else "AI-DEP-001"
            violations.append(
                ComplianceViolation(
                    rule_id,
                    str(package_json_path.relative_to(root_dir)),
                    f"Unauthorized Node.js runtime dependency detected: '{pkg_name}'",
                )
            )

    # Inspect package-lock.json if present
    lock_path = root_dir / "apps" / "web" / "package-lock.json"
    if lock_path.exists():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            packages = lock_data.get("packages", {})
            for pkg_path, pkg_info in packages.items():
                name = pkg_info.get("name") or pkg_path.split("node_modules/")[-1]
                if name and name.lower() in PROHIBITED_NODE_PACKAGES:
                    violations.append(
                        ComplianceViolation(
                            "LOCK-001",
                            str(lock_path.relative_to(root_dir)),
                            f"Unauthorized package found in package-lock.json: '{name}'",
                        )
                    )
        except Exception:
            pass

    return violations


def check_executable_python_code(root_dir: Path) -> list[ComplianceViolation]:
    violations = []
    
    for dir_name in EXECUTABLE_DIRS:
        target_dir = root_dir / dir_name
        if not target_dir.exists():
            continue

        for py_file in target_dir.glob("**/*.py"):
            if ".venv" in py_file.parts or "node_modules" in py_file.parts or "tests" in py_file.parts or py_file.name.startswith("test_"):
                continue

            rel_path = str(py_file.relative_to(root_dir))
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            lines = content.splitlines()
            for line_no, line in enumerate(lines, 1):
                clean_line = line.split("#")[0]  # ignore comments
                for sym in PROHIBITED_OPENCV_SYMBOLS:
                    if sym in clean_line:
                        violations.append(
                            ComplianceViolation(
                                "CV-001",
                                f"{rel_path}:{line_no}",
                                f"Prohibited OpenCV API detected: '{sym}'",
                            )
                        )

            try:
                tree = ast.parse(content, filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_mod = alias.name.split(".")[0].lower()
                            if root_mod in PROHIBITED_PYTHON_IMPORTS:
                                violations.append(
                                    ComplianceViolation(
                                        PROHIBITED_PYTHON_IMPORTS[root_mod],
                                        f"{rel_path}:{node.lineno}",
                                        f"Prohibited Python import detected: 'import {alias.name}'",
                                    )
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_mod = node.module.split(".")[0].lower()
                            if root_mod in PROHIBITED_PYTHON_IMPORTS:
                                violations.append(
                                    ComplianceViolation(
                                        PROHIBITED_PYTHON_IMPORTS[root_mod],
                                        f"{rel_path}:{node.lineno}",
                                        f"Prohibited Python import detected: 'from {node.module} import ...'",
                                    )
                                )
            except SyntaxError:
                pass

    return violations


def check_executable_js_ts_code(root_dir: Path) -> list[ComplianceViolation]:
    violations = []
    web_dir = root_dir / "apps" / "web"
    if not web_dir.exists():
        return violations

    for ext in ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.mjs"]:
        for code_file in web_dir.glob(ext):
            if "node_modules" in code_file.parts or ".next" in code_file.parts or "tests" in code_file.parts or code_file.name.startswith("test_"):
                continue

            rel_path = str(code_file.relative_to(root_dir))
            try:
                content = code_file.read_text(encoding="utf-8")
            except Exception:
                continue

            lines = content.splitlines()
            for line_no, line in enumerate(lines, 1):
                clean_line = line.split("//")[0]
                for pkg in PROHIBITED_NODE_PACKAGES:
                    pattern = rf"from\s+['\"]{re.escape(pkg)}['\"]|import\s+.*['\"]{re.escape(pkg)}['\"]"
                    if re.search(pattern, clean_line):
                        rule_id = "AGENT-DEP-001" if "langchain" in pkg or "crewai" in pkg or "autogen" in pkg else "AI-IMP-001"
                        violations.append(
                            ComplianceViolation(
                                rule_id,
                                f"{rel_path}:{line_no}",
                                f"Prohibited JS/TS import detected: '{pkg}'",
                            )
                        )

    return violations


def check_env_and_secrets(root_dir: Path) -> list[ComplianceViolation]:
    violations = []

    gitignore_path = root_dir / ".gitignore"
    if gitignore_path.exists():
        gi_content = gitignore_path.read_text(encoding="utf-8")
        if not re.search(r"^\.env$", gi_content, re.MULTILINE) and not re.search(r"^\.env\b", gi_content, re.MULTILINE):
            violations.append(
                ComplianceViolation(
                    "SECRET-001",
                    ".gitignore",
                    "Missing '.env' entry in .gitignore file",
                )
            )

    env_example_path = root_dir / ".env.example"
    if not env_example_path.exists():
        violations.append(
            ComplianceViolation(
                "ENV-001",
                ".env.example",
                "Required file '.env.example' is missing",
            )
        )
    else:
        content = env_example_path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), 1):
            line_str = line.strip()
            if line_str and not line_str.startswith("#") and "=" in line_str:
                k, v = line_str.split("=", 1)
                k_str = k.strip()
                v_str = v.strip()
                if len(v_str) > 20 and not v_str.startswith("http") and not v_str.startswith("gs://") and " " not in v_str:
                    violations.append(
                        ComplianceViolation(
                            "ENV-001",
                            f".env.example:{line_no}",
                            f"Possible secret value assigned in .env.example for key '{k_str}'",
                        )
                    )

    return violations


def run_compliance_gate(target_dir: Path = ROOT_DIR) -> tuple[int, list[ComplianceViolation]]:
    violations = []
    violations.extend(check_python_dependencies(target_dir))
    violations.extend(check_node_dependencies(target_dir))
    violations.extend(check_executable_python_code(target_dir))
    violations.extend(check_executable_js_ts_code(target_dir))
    violations.extend(check_env_and_secrets(target_dir))

    return (len(violations), violations)


def main():
    print("=" * 60)
    print("SceneRights AI Compliance Gate (v6.2.2 Baseline)")
    print("=" * 60)

    count, violations = run_compliance_gate(ROOT_DIR)

    if count == 0:
        print("[PASS] All compliance gate checks passed cleanly.")
        sys.exit(0)
    else:
        print(f"[FAIL] Found {count} compliance violation(s):\n")
        for v in violations:
            print(f"  {v}")
        print("\nCompliance gate failed. Fix offending dependencies or imports before committing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
