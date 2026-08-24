# SceneRights AI — Milestone 1D Compliance Baseline Specification

**Project:** SceneRights AI  
**Milestone:** 1D — Compliance Baseline  
**Master Specification:** SceneRights AI v6.2.2  
**Scope:** P0  
**Status:** Implementation Specification

---

# 1. Authority

This document defines the implementation requirements for Milestone 1D only.

The authoritative source of truth remains:

`SceneRights_AI_v6_2_2_Master_Spec.md`

If this document conflicts with the v6.2.2 Master Spec, the Master Spec wins.

No requirement in this document may be interpreted as permission to expand P0 scope.

---

# 2. Milestone Goal

Milestone 1D establishes automated repository compliance controls before Gemini, media analysis, MCP runtime integration, and other higher-level application functionality are implemented.

The milestone must prevent accidental introduction of:

- unauthorized AI providers,
- unauthorized agent frameworks,
- unauthorized computer-vision inference,
- secrets or credentials,
- unsafe dependency changes,
- prohibited runtime integrations.

The compliance system must be suitable for local development and CI.

---

# 3. Scope

Milestone 1D SHALL implement:

1. Python dependency compliance checking.
2. Node.js dependency compliance checking.
3. Prohibited AI provider/framework detection.
4. OpenCV prohibited-inference detection.
5. Secret scanning integration.
6. GitHub Actions CI.
7. Compliance tests.
8. Compliance documentation.

Milestone 1D SHALL NOT implement:

- Gemini calls,
- Vertex AI calls,
- Google ADK agents,
- Agent Engine deployment,
- Cloud Storage uploads,
- policy extraction,
- FFmpeg processing,
- continuity analysis,
- MCP runtime connectivity,
- agent queries,
- frontend feature development,
- production deployment.

---

# 4. Compliance Philosophy

Compliance must be enforced structurally.

The primary enforcement mechanism SHALL be:

- dependency allowlisting,
- package manifest inspection,
- lockfile inspection,
- runtime import/configuration inspection.

Keyword scanning SHALL NOT be the sole or primary AI compliance mechanism.

Keyword scanning MAY be used as a secondary warning-oriented defense.

Comments and documentation mentioning prohibited technologies must not automatically cause a misleading compliance failure unless they demonstrate actual runtime use.

---

# 5. Permitted AI Runtime

SceneRights AI runtime AI is restricted to the Google ecosystem defined by the Master Spec.

Permitted AI SDK/framework dependencies include:

- `google-genai`
- `google-adk`

Permitted runtime AI services include:

- Gemini
- Vertex AI
- Google ADK
- Google Agent Engine where required by later milestones

No AI integration is implemented during Milestone 1D itself.

The compliance gate is preparing enforcement for later milestones.

---

# 6. Prohibited AI Runtime Providers

The application runtime SHALL NOT introduce dependencies, imports, configuration, API clients, or inference calls for unauthorized AI providers.

Examples that SHALL be rejected when detected as runtime dependencies or imports include:

- OpenAI
- Anthropic / Claude SDK
- Cohere
- Mistral AI
- Groq
- Together AI
- Hugging Face inference services
- AWS Bedrock
- Azure OpenAI
- Microsoft-hosted AI inference
- other external LLM/inference providers not authorized by the Master Spec

The compliance implementation SHOULD distinguish between:

1. actual runtime dependency/import usage, and
2. harmless textual references in documentation, comments, test fixtures, or compliance rules.

The second category must not automatically fail CI.

---

# 7. Prohibited Agent Frameworks

The runtime SHALL NOT use third-party agent orchestration frameworks including:

- LangChain
- LangGraph
- CrewAI
- AutoGen
- Semantic Kernel
- other external agent frameworks that replace the Google ADK architecture defined by the Master Spec.

The compliance gate SHALL detect these through dependency and runtime import inspection.

---

# 8. Python Dependency Allowlist

The compliance gate SHALL inspect:

`services/api/pyproject.toml`

and any authoritative Python lockfile introduced by the repository.

Dependencies must correspond to functionality permitted by the Master Spec.

Expected permitted backend dependencies include, as applicable to the relevant implemented milestone:

- `fastapi`
- `uvicorn`
- `pydantic`
- `pydantic-settings`
- `clickhouse-connect`
- `google-genai`
- `google-adk`
- `google-cloud-storage`
- `opencv-python-headless`
- `pypdf`
- `python-docx`
- `python-multipart`
- `pytest`
- `pytest-asyncio`
- `httpx`

This list must not be interpreted as requiring installation of every dependency during Milestone 1D.

Dependencies SHALL only be installed when needed by the implemented milestone.

Standard build/development dependencies required by the Python toolchain may be permitted where appropriate.

Unexpected runtime dependencies SHALL cause the compliance gate to fail unless explicitly approved and consistent with the Master Spec.

---

# 9. Node.js Dependency Allowlist

The compliance gate SHALL inspect:

`apps/web/package.json`

and:

`apps/web/package-lock.json`

Expected permitted frontend dependencies include, as applicable:

- `next`
- `react`
- `react-dom`
- `typescript`
- `@types/react`
- `@types/node`
- `tailwindcss`
- `clsx`
- `tailwind-merge`
- `lucide-react`

Framework-required development/build dependencies may be allowed where necessary.

The compliance implementation SHALL NOT require installation of unused packages merely because they appear in this specification.

Unexpected runtime packages must be identified.

Unauthorized AI SDKs must fail compliance.

---

# 10. Lockfile Inspection

Compliance checks SHALL inspect package lock information rather than trusting only top-level dependency declarations.

For Node.js:

`package-lock.json`

must be inspected.

If a Python lockfile is introduced, it must also be inspected.

The purpose is to detect unauthorized runtime packages that may enter through dependency changes.

The implementation must avoid false failures from unrelated package names unless they actually represent prohibited runtime functionality.

---

# 11. OpenCV Restrictions

OpenCV may later be used only for deterministic image-processing operations permitted by the Master Spec.

It SHALL NOT be used as an alternative AI inference system.

The compliance gate SHALL reject runtime usage of prohibited OpenCV inference APIs including:

`cv2.dnn`

The gate SHALL also detect prohibited model/inference mechanisms identified by the Master Spec, including where applicable:

`cv2.CascadeClassifier`

`cv2.face`

The scanner must inspect executable source code.

References appearing solely inside:

- documentation,
- compliance rules,
- comments explaining prohibited APIs,
- test fixtures designed to verify the scanner,

must be handled carefully so the compliance system does not fail itself.

---

# 12. Secret Protection

No secret may be committed to Git.

Protected values include:

- Google Cloud credentials,
- service-account private keys,
- Gemini/Vertex credentials,
- ClickHouse passwords,
- ClickHouse connection secrets,
- MCP authentication tokens,
- demo access tokens,
- API keys,
- private certificates,
- OAuth secrets,
- signed credentials.

`.env.example` SHALL contain variable names and safe placeholders only.

Real credentials SHALL remain in ignored local `.env` files or approved cloud secret-management systems.

---

# 13. Required `.gitignore` Protection

The repository SHALL ignore sensitive/local files including appropriate patterns for:

`.env`

`.env.*`

while explicitly permitting:

`!.env.example`

It SHALL also ignore local/generated artifacts as appropriate, including:

- Python virtual environments,
- Python cache files,
- Node modules,
- Next.js build output,
- local media artifacts where appropriate,
- local credential files.

The implementation must verify that `.env.example` remains tracked.

---

# 14. Secret Scanner

Milestone 1D SHALL integrate `gitleaks` as the repository secret scanner.

The implementation SHALL provide a documented way to run secret scanning locally.

CI SHALL run secret scanning automatically.

The scanner must inspect repository content for accidental credentials before code is accepted.

The implementation must not print real secret values during testing.

No test may require committing an actual secret.

Synthetic fake-secret fixtures may be used where necessary.

---

# 15. Compliance Gate Script

Create:

`scripts/compliance_gate.py`

The script SHALL perform the repository-specific compliance checks required by this milestone.

At minimum it SHALL:

1. inspect Python dependency declarations,
2. inspect Node dependency declarations,
3. inspect relevant lockfiles,
4. identify prohibited AI SDK dependencies,
5. identify prohibited agent-framework dependencies,
6. inspect executable Python/TypeScript/JavaScript source for prohibited runtime imports,
7. inspect executable code for prohibited OpenCV inference APIs,
8. verify required secret-protection patterns,
9. verify `.env.example` contains no real secrets,
10. produce a clear pass/fail result.

Successful execution SHALL return process exit code:

`0`

A compliance violation SHALL return a non-zero process exit code.

---

# 16. Scanner Scope

The scanner SHOULD inspect executable project areas including:

- `services/`
- `agents/`
- `tools/`
- `apps/`

The scanner SHOULD avoid treating the following as runtime violations merely because prohibited technology names appear there:

- `docs/`
- Master specification documents,
- compliance documentation,
- scanner source definitions,
- test fixtures explicitly testing prohibited patterns.

Dependency manifests and lockfiles remain authoritative regardless of documentation exclusions.

---

# 17. Error Reporting

Compliance failures SHALL be understandable.

A failure should identify:

- compliance rule,
- affected file,
- offending dependency/import/API where safe,
- remediation category.

Example conceptual output:

`FAIL AI-DEP-001: Unauthorized runtime AI dependency detected in services/api/pyproject.toml`

The compliance script SHALL NOT expose credentials when reporting secret-related failures.

---

# 18. Compliance Rule IDs

Use stable rule identifiers where practical.

Recommended identifiers:

- `AI-DEP-001` — prohibited AI dependency
- `AI-IMP-001` — prohibited AI runtime import
- `AGENT-DEP-001` — prohibited agent framework
- `CV-001` — prohibited OpenCV inference API
- `SECRET-001` — possible committed secret
- `ENV-001` — unsafe environment-file configuration
- `LOCK-001` — unauthorized package found through lockfile inspection

Additional rule IDs may be introduced if necessary.

---

# 19. GitHub Actions CI

Create a GitHub Actions workflow under:

`.github/workflows/ci.yml`

The workflow SHALL run on:

- pull requests,
- pushes to `main`.

The CI workflow SHALL include appropriate jobs/steps for:

1. repository checkout,
2. supported Python setup,
3. supported Node.js setup,
4. backend dependency installation,
5. frontend dependency installation,
6. SceneRights compliance gate,
7. backend tests,
8. frontend production build,
9. secret scanning.

CI must fail if a mandatory compliance check fails.

---

# 20. CI Credential Safety

Milestone 1D CI SHALL NOT require production credentials.

CI SHALL NOT require:

- real ClickHouse passwords,
- GCP service-account keys,
- Gemini credentials,
- MCP tokens.

Tests requiring real cloud services must remain separate from baseline compliance CI unless securely configured in a later milestone.

Milestone 1D CI must be capable of running against the repository without exposing cloud secrets.

---

# 21. Compliance Tests

Add automated tests for the compliance gate.

At minimum test:

## TEST-COMP-001 — Allowed Python dependency

Known permitted dependency passes.

## TEST-COMP-002 — Prohibited AI dependency

Synthetic prohibited AI runtime dependency fails.

## TEST-COMP-003 — Prohibited agent framework

Synthetic prohibited agent-framework dependency fails.

## TEST-COMP-004 — Prohibited runtime import

Synthetic unauthorized AI import fails.

## TEST-COMP-005 — Documentation reference

Mentioning a prohibited provider in documentation does not itself fail runtime compliance.

## TEST-COMP-006 — OpenCV DNN

Synthetic executable usage of:

`cv2.dnn`

fails.

## TEST-COMP-007 — Compliance scanner self-reference

The compliance script's own prohibited-pattern definitions do not cause the repository to fail.

## TEST-COMP-008 — `.env` protection

Gitignore protection for real `.env` files is validated.

## TEST-COMP-009 — `.env.example`

Safe placeholder `.env.example` passes.

## TEST-COMP-010 — Exit status

A compliant repository returns exit code 0.

A synthetic violating fixture returns non-zero.

---

# 22. Existing Milestone Protection

Milestone 1D must not break Milestones 1A–1C.

After implementation:

- FastAPI health endpoint must still work.
- Existing Pydantic/schema tests must pass.
- Existing ClickHouse repository tests must pass.
- Next.js production build must pass.
- Existing ClickHouse architecture must remain unchanged.

No schema redesign is permitted in this milestone.

---

# 23. No Functional Product Changes

Milestone 1D is infrastructure/compliance work.

The visual UI at:

`localhost:3000`

is expected to remain unchanged.

Do not redesign the dashboard.

Do not add mock product functionality simply to make the frontend appear more complete.

---

# 24. Expected File Changes

Expected additions may include:

```text
scripts/
└── compliance_gate.py

.github/
└── workflows/
    └── ci.yml

services/api/tests/
└── test_compliance_gate.py

docs/
└── compliance.md