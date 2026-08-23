# SceneRights AI v6.2.2 --- Hackathon-Compliant Implementation Specification

## Agentic Production Compliance, Continuity, Policy Intelligence & Visual Review

**Competition:** Agentic Cinema: The Blockbuster Hackathon\
**Track:** ClickHouse\
**Specification Status:** v6.2.2 --- supersedes v6.2.1, v6.2, v6.1, and v6 in full\
**Submission Deadline:** September 9, 2026, 2:00 PM PT\
**Google Cloud credit request deadline:** August 31, 2026, 11:59 PM PST\
**Primary Goal:** Build a functional web-based AI agent for
studio/filmmaker workflows using only permitted Google Cloud AI plus the
required partner technology, scoped to what an 18-day build window can
actually ship.

------------------------------------------------------------------------

# 0. Changelog

## v6.2.2 from v6.2.1

v6.2.2 is an implementation-lock patch. It does **not** change the P0
product scope, demo story, AI architecture, or five-screen UI.

**Persistence / API alignment**
- Added a minimal authoritative `policy_documents` table so the existing
  `policy_id` API contract has a concrete persisted resource for filename,
  GCS URI, processing status, and timestamps.
- Added `policy_id` to `policy_rules` so every extracted rule is linked to
  the uploaded policy document that produced it.
- Added a minimal authoritative `scenes` table with `reference_clip_id` so
  the existing scene/reference APIs have a concrete persisted state.

**MCP credential separation**
- Added a dedicated environment block for the `mcp-clickhouse` Cloud Run
  service. The MCP service uses the `scenerights_mcp_ro` ClickHouse user
  with SELECT-only access to scoped views and never reuses the FastAPI
  application's write-capable ClickHouse credentials.

**Agent-run logging ownership**
- Clarified that `agent_runs` is written by the FastAPI/agent orchestration
  layer through the application write connection **after** each MCP tool
  call returns. The MCP server itself remains read-only and does not write
  audit rows.

No other implementation behavior changes in v6.2.2.

## v6.2 from v6.1

v6.2 is a focused implementation-readiness cleanup. It does **not**
expand the hackathon P0 scope. The v6.1 product architecture,
five-screen UI, twelve core use cases, ClickHouse MCP design, and
three-minute demo remain the source of truth.

**AI quality / determinism** - Replaced the overly strict requirement
that repeated Gemini calls produce byte-for-byte identical output.
Repeated runs are now evaluated for **semantic classification
stability** on the controlled demo set. - Explanation wording may vary;
the required object-state classification must remain stable within the
acceptance threshold defined in the AI quality test plan.

**AI-compliance CI gate** - Replaced keyword grep as the primary
prohibited-AI control with a dependency allowlist and lockfile/package
inspection. - Keyword scanning remains a secondary warning-oriented
check so comments, documentation, and defensive code do not create
misleading compliance failures. - Runtime imports/configuration still
fail CI if they introduce a prohibited AI provider, inference SDK, or
agent framework.

**ClickHouse current-state view** - Clarified that `findings_current`
derives the latest human review state from the append-only `decisions`
log using an explicit latest-decision subquery before joining to
findings. This avoids relying on aggregate behavior over a LEFT JOIN for
the demo-critical state transition. - The demo invariant remains: one
decision INSERT must be reflected by the next current-state SELECT
without mutation delay.

**API / schema consistency** - Clarified the distinction between
`policy_id` (uploaded document/workflow identifier) and `policy_rule_id`
(individual extracted rule identifier). - Added an implementation gate
requiring endpoint DTOs, ClickHouse columns, enums, and Pydantic schemas
to use the authoritative vocabulary in this specification before
frontend integration begins.

**Security positioning** - Clarified that the shared demo-access token
is a hackathon-only access control, not production-grade authentication
or a claim of enterprise multi-tenant security.

No new P0 feature is introduced by v6.2.

## v6.1 from v6

v6.1 resolved the CRITICAL and HIGH findings from the v6 audit and the
MEDIUM findings incorporated into that revision. Authentication is
explicitly **not** built --- see §33.

**Structural** - Deleted duplicate §16 (ClickHouse Schema --- MVP);
§38-equivalent (now §16, this doc) is the single authoritative schema. -
Merged three competing demo scripts (old §25, §53, §73) into one: §25
here. - Merged three Definition of Done checklists into one: §27 here. -
Deleted the phantom "Deterministic Edit → Gemini QA Review" stage from
the architecture diagram (old §2). - Deleted duplicated
Gemini-responsibilities and MVP-scope lists, keeping the more complete
version and reconciling both against actual P0 scope. - Added §26
(Delivery Schedule) and §27 renamed appropriately; added §31
(Post-Hackathon Roadmap) to hold everything cut from P0 so nothing is
silently dropped.

**Schema / data (CRITICAL)** - `findings` and `decisions` are now
**append-only**. Current state is derived via a `findings_current` VIEW
using `argMax`. Plain `MergeTree` cannot support the required "resolve →
re-query reflects change" demo beat via `ALTER … UPDATE` --- that path
is removed entirely. - Added missing tables: `clips`, `analysis_runs`,
`agent_runs`. Dropped `organizations`/`users`/`policy_documents` as
separate ClickHouse tables for the MVP (see §33, §14 data model) ---
demo runs single-tenant, single-org. - `policy_rules` gains
`source_quote`, `version`, `effective_date`. - `findings` gains
`analysis_run_id`, `policy_rule_version`, `source_quote` reference, and
splits `status` into `ai_assessment` and `review_status` (see
status-vocabulary fix below). - Reconciled `rule_id` / `policy_rule_id`
naming --- `policy_rule_id` used everywhere, including endpoint paths.

**Status vocabulary (HIGH)** - Single vocabulary now used everywhere:
`ai_assessment` ∈ {`present`, `absent`, `not_visible`, `changed`,
`uncertain`} written once by the pipeline; `review_status` ∈ {`open`,
`confirmed`, `not_issue`, `escalated`, `resolved`} written only by
humans via `decisions` inserts. The old `needs_human_review` /
`needs_review` / `Awaiting Approval` mix is gone.

**Media path (CRITICAL)** - Gemini receives **paired keyframes**, not
raw video. FFmpeg extracts 3--5 frames per clip at fixed timestamps;
each reference/comparison pair goes to Gemini in one structured-output
call with the approved rule set in context. Output is a closed enum, not
free text.

**Auth (CRITICAL --- resolved by explicit decision, not by building
it)** - **No login/signup is built.** Single seeded organization, single
seeded project, single shared demo-access token, all API queries
server-side scoped to the seeded `project_id`. See §33.

**MCP / security (CRITICAL)** - Transport fixed to Streamable HTTP;
`mcp-clickhouse` deployed as its own Cloud Run service. - chDB tools
disabled (`CHDB_ENABLED=false`); ADK `tool_filter` restricts the agent
to `run_select_query` and `list_tables` only. - Read-only enforced at
the ClickHouse user grant (`scenerights_mcp_ro`, `SELECT`-only,
`readonly=1` in the user profile), not only via the MCP server's
write-access flag. - The MCP user sees only pre-filtered views scoped to
the demo project --- not base tables --- closing the tenant-isolation
gap that existed even with correct MCP config.

**Scope (HIGH)** - MVP cut from 50 FRs / 30 UCs / 27 components / 7
screens / 8 tables down to a 20-FR / 12-UC / 14-component / 5-screen /
7-table P0. Every cut item is preserved in §31 (Post-Hackathon Roadmap),
not deleted. - License-plate detection removed from scope and demo
assets (trademark/privacy exposure in the video rules). Fictional-logo
detection covers the same "policy branch, not continuity branch"
demonstration point without the exposure. - Earring detection and
jewelry-style/colour-change detection removed from P0 (HIGH
false-positive risk); necklace presence, mug colour, and one occlusion
case are the three continuity beats.

**Other** - Severity is now derived deterministically from the matched
policy rule's `priority`, not emitted by Gemini. - Confidence is a
three-value enum (`clear` / `likely` / `uncertain`), labelled "model
assessment," not a percentage. - Report generation and "QA final
reports" are deterministic templating from ClickHouse rows --- no Gemini
call. - Added prompts directory (§19), async job model + missing GET
endpoints (§39), error envelope (§45), idempotency (§39), NFR targets
(§35), new tests (§42), video-content prompt-injection handling (§7,
§41). - Removed unused/undecided technology mentions: Node/TypeScript
backend option, Firestore/Cloud SQL/BigQuery ML, generative-repair hedge
language.

------------------------------------------------------------------------

# 1. Competition Compliance Baseline

## Mandatory AI Rule

The competition build may use only:

1.  Google Cloud artificial intelligence tools permitted by the contest
    (Gemini via Vertex AI / Agent Builder / Agent Engine, permitted
    Vertex AI services, BigQuery ML if actually used --- it is not).
2.  Built-in AI-powered features of the selected Partner product
    relevant to the ClickHouse track.

The competition build must **not** use any other AI model, AI API, agent
framework, external embedding model, third-party computer-vision AI
model, or external generative image/video model --- including but not
limited to OpenAI/GPT, Anthropic/Claude, AWS AI, Microsoft AI,
LangChain/CrewAI/AutoGen as agent frameworks, and any external Hugging
Face inference models.

Development tooling (e.g. an AI coding assistant used to help write this
spec or the code) is out of scope for this restriction, which applies to
the submitted **runtime**. No such tooling appears in the submitted
dependency tree, README technology list, or configuration.

Non-AI third-party software remains allowed, subject to its own license:
Next.js, React, TypeScript, Python, FastAPI, FFmpeg, deterministic
OpenCV operations (see §29 --- explicitly excludes `cv2.dnn` and
pretrained classifiers), standard databases, standard web libraries.

------------------------------------------------------------------------

# 2. Required Competition Architecture

``` text
                COMPANY / STUDIO
                       │
          ┌────────────┴────────────┐
          │                         │
   Policy Documents             Video Takes
          │                         │
          └────────────┬────────────┘
                       ▼
              Google Cloud Storage
                       │
                       ▼
          Gemini (Vertex AI) — Analysis Pipeline
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
 Policy Extraction  FFmpeg Keyframes  Continuity Compare
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                Finding Engine
                       │
        ┌──────────────┴──────────────┐
        ▼ WRITE LANE                  ▼ READ LANE
  FastAPI → clickhouse-connect   Gemini Agent (ADK)
        │                              │
        ▼                              ▼
                 ClickHouse Cloud
                 (findings, decisions,
                  findings_current view)
                        ▲
                        │ mcp-clickhouse
                        │ (Streamable HTTP,
                        │  read-only user,
                        │  scoped views)
                        │
                 Gemini Agent (ADK)
                        │
                        ▼
                  Human Review
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
       Resolve                    Escalate
          │
          ▼
   INSERT into decisions
          │
          ▼
  Deterministic Report Template
```

**Two explicit lanes.** Writes (new findings, human decisions) go
through the FastAPI backend directly to ClickHouse. Reads for the
agent's current-state questions go through the official `mcp-clickhouse`
server, which is read-only by grant, not just by configuration flag. The
MCP server is never used to write. There is no "generative repair" or
"Gemini QA review" stage in the runtime --- see §13 and §31.

------------------------------------------------------------------------

# 3. AI / Non-AI Component Matrix

  -----------------------------------------------------------------------------
  Component                     Classification          Competition Build
  ----------------------------- ----------------------- -----------------------
  Gemini multimodal analysis    Google AI               Allowed
  (paired keyframes)                                    

  Gemini policy reasoning       Google AI               Allowed

  Google ADK + Agent Engine     Google AI/agent tooling Allowed, required

  ClickHouse MCP (official      Partner runtime         Required for ClickHouse
  `mcp-clickhouse`)             requirement             track

  ClickHouse Cloud              Partner data platform   Required

  FFmpeg                        Non-AI                  Allowed

  OpenCV --- deterministic      Non-AI                  Allowed
  transforms only (no                                   
  `cv2.dnn`, no classifiers)                            

  Next.js / React / TypeScript  Non-AI                  Allowed
  / Tailwind                                            

  FastAPI / Pydantic / Uvicorn  Non-AI                  Allowed

  Cloud Run                     Infrastructure          Allowed

  Cloud Storage                 Infrastructure          Allowed

  Secret Manager                Infrastructure          Allowed

  Cloud Logging                 Infrastructure          Allowed

  OpenAI / Anthropic / AWS AI / External AI             Prohibited
  Microsoft AI                                          

  External                      External AI             Prohibited
  vision/embedding/generative                           
  models                                                

  LangChain / CrewAI / AutoGen  External agent          Prohibited
                                framework               
  -----------------------------------------------------------------------------

**Engineering rule:** every dependency that performs inference,
embeddings, generative processing, autonomous planning, or AI-based
classification requires an explicit compliance review before being
added. A CI dependency/compliance gate enforces this --- see §29.

------------------------------------------------------------------------

# 4. Product Definition

SceneRights AI is a Gemini-powered production supervisor for filmmakers
and studio crews. Two workflows are built for the hackathon (a third,
visual/privacy review, is exercised only through the fictional-logo case
--- see §31 for the fuller scope):

## A. Company Policy Intelligence

Studios upload a short policy document. Gemini extracts structured
candidate rules with a verbatim source quote from the document; a human
approves each rule before it becomes enforceable.

## B. Cross-Shot Continuity (primary demo capability)

Gemini compares a reference take and a comparison take for a small,
deliberately narrow set of tracked items --- necklace presence, mug
colour --- and distinguishes genuinely missing/changed from merely
not-visible.

## C. Policy-Grounded Visual Review (secondary demo capability)

One additional detection --- a fictional unapproved logo ---
demonstrates that the same policy-matching mechanism generalizes beyond
continuity, without requiring the license-plate/PII exposure of the
original scope (see §31).

Findings are always checked against approved policy and always presented
to a human before being treated as final. The system never issues a
legal or trademark conclusion.

------------------------------------------------------------------------

# 5. ClickHouse Track Design

The ClickHouse track requires the submission to actively use ClickHouse
at runtime through the official `mcp-clickhouse` MCP server, connected
to ClickHouse Cloud. This design satisfies that requirement with an
architecture that is also, independently, the right way to use
ClickHouse for this workload:

-   **Findings are an append-only event log**, not a mutable row store.
    Current state (`findings_current`) is *reconstructed* via
    `argMax(review_status, created_at)` over the `decisions` log. This
    is idiomatic ClickHouse --- event history plus derived current state
    --- and it is also what makes the demo's state-change beat reliable:
    an `INSERT` is visible to the next `SELECT` immediately, unlike an
    `ALTER … UPDATE` mutation.
-   **The agent only ever reads.** All state changes happen through the
    FastAPI backend, which validates authorization and writes an
    immutable decision record. The MCP server's ClickHouse user has no
    `INSERT`/`ALTER`/`DROP` grant at all --- not merely a flag that
    could be flipped.
-   **The agent's ClickHouse user sees only pre-filtered views**, scoped
    to the single seeded demo project, not base tables. Even a maximally
    adversarial or prompt-injected query cannot read outside the demo
    project's data because the underlying rows are not visible to that
    database user.

## Runtime Agent Questions

``` text
Show unresolved high-priority findings in Scene 12.
Which continuity objects changed between Take A and Take B?
How many findings remain open?
What does the studio policy say about logos?
```

## Making the integration impossible to miss

-   Every agent answer is accompanied by a permanent **data-source
    chip**: `ClickHouse MCP · run_select_query · N rows · Xms`.
-   The agent panel includes an **MCP Activity rail**: tool name →
    argument summary → formatted read-only SQL → row count → latency,
    rendered as a live instrument readout, not a chat log.
-   `mcp-clickhouse` is deployed as its own named Cloud Run service
    (`scenerights-mcp-clickhouse`), visible in the console and in the
    architecture diagram.
-   The dashboard shows a running `agent_runs` counter for the session.

------------------------------------------------------------------------

# 6. Competition-Safe MVP --- Golden Path

``` text
1. COMPANY UPLOADS POLICY FILE
             ↓
2. GEMINI EXTRACTS RULES (with verbatim source_quote)
             ↓
3. HUMAN APPROVES RULES
             ↓
4. USER UPLOADS TAKE A + TAKE B (+ occlusion take C)
             ↓
5. TAKE A SET AS CONTINUITY REFERENCE
             ↓
6. FFMPEG EXTRACTS KEYFRAME PAIRS
             ↓
7. GEMINI COMPARES PAIRED FRAMES → closed-enum ai_assessment
             ↓
8. SEVERITY DERIVED FROM MATCHED RULE PRIORITY
             ↓
9. FINDINGS WRITTEN (APPEND-ONLY) TO CLICKHOUSE
             ↓
10. AGENT QUERIES findings_current THROUGH CLICKHOUSE MCP
             ↓
11. HUMAN REVIEWS FINDINGS → decision INSERTed
             ↓
12. AGENT RE-QUERIES → answer reflects new state (same turn/session)
             ↓
13. DETERMINISTIC REPORT TEMPLATE
```

This is the entire P0 scope. See §26 for dates and §28 for the priority
matrix.

------------------------------------------------------------------------

# 7. Demo Policy, Footage, and Findings

## Demo Policy (fictional)

``` text
NORTHSTAR STUDIOS — SCENE 12 POLICY

Continuity:
1. Lead actor wears a silver necklace throughout Scene 12. (priority: high)
2. Hero mug remains blue throughout Scene 12. (priority: high)

Visual Review:
3. Flag visible unapproved fictional logos. (priority: medium)
```

Two continuity rules and one visual-review rule --- three rules total,
consistent everywhere in this document (resolves the 3-vs-6
inconsistency in v6).

Use only fictional names and original content. Uploaded text --- both
this policy document and any text visible inside the video footage ---
is treated as **untrusted data**, never as instructions. See §41.

## Demo Footage --- three original clips

**Take A --- Reference:** silver necklace clearly visible, blue mug,
fictional logo prop absent, medium-close static framing, matched
lighting, ≥1080p.

**Take B --- Comparison:** necklace absent, mug changed to red,
fictional logo card visible in background.

**Take C --- Occlusion:** necklace present but obscured by hair/scarf
--- used to demonstrate that the system reports `not_visible`, never
`absent`.

Shoot with a team member as the on-camera performer (avoids third-party
publicity-rights exposure) and sweep every frame for incidental
third-party brands. **No real vehicle or license plate appears in any
demo asset** (see §31 --- cut for compliance risk, not just
feasibility).

## Expected Findings

``` text
CONTINUITY — HIGH (from policy rule 1, priority: high)
Silver necklace: present in Take A, ai_assessment=absent in Take B.

CONTINUITY — HIGH (from policy rule 2, priority: high)
Hero mug: blue in Take A, ai_assessment=changed (red) in Take B.

VISUAL REVIEW — MEDIUM (from policy rule 3, priority: medium)
Possible unapproved fictional logo detected in Take B.

CONTINUITY — (Take C only, demo-only beat, not a "finding")
Necklace region: ai_assessment=not_visible. Explicitly not reported
as a finding requiring resolution — surfaced as a system capability,
not a flagged issue.
```

------------------------------------------------------------------------

# 8. Human-in-the-Loop Requirement

The system distinguishes four things at all times, and every finding UI
element keeps them visually separate:

``` text
OBSERVATION       What Gemini saw (ai_assessment, from paired frames)
POLICY            The approved rule's verbatim source_quote
INTERPRETATION    Why the observation may conflict with policy
DECISION          What the human reviewer decided (review_status)
```

Example:

``` text
Observation:  Red mug detected (ai_assessment=changed).
Policy:       "Hero mug remains blue throughout Scene 12." (priority: high)
Interpretation: Possible continuity conflict.
Decision:     Confirmed by script supervisor. (review_status=confirmed)
```

No finding is final without a human decision. No extracted policy rule
is enforceable without human approval.

------------------------------------------------------------------------

# 9. Policy Grounding Requirements

The AI must not invent company policy. Every policy-grounded finding
cites:

``` text
document name
policy_rule_id
rule text
source_quote (verbatim substring of the extracted document text)
```

**Enforcement, not just intent:** at extraction time, Gemini emits
`source_quote` for each candidate rule; the backend validates it as an
exact substring of the parsed document text before the rule can be shown
for approval. A rule whose `source_quote` fails validation is rejected
automatically and never reaches the approval queue. This closes the
hallucination path structurally rather than by policy statement alone.

If no matching approved rule exists for an observation:

``` text
No applicable company policy found.
Human review may still be appropriate.
```

Policy conflict detection, versioning, and scope hierarchy are
explicitly out of P0 --- see §31.

------------------------------------------------------------------------

# 10. Privacy and Company Documents

Uploaded policy documents and video are:

-   stored in Cloud Storage, private by default, accessed only via
    short-lived signed URLs generated per request (15-minute TTL),
-   excluded from the public repository,
-   never logged in full (structured logs redact prompt/document
    bodies).

Never commit: real confidential studio policies, API secrets, private
footage, credentials, customer data. The public repository ships only
the fictional Northstar policy and the three original demo clips.

------------------------------------------------------------------------

# 11. Media Processing Strategy

Sophisticated generative video repair is **not part of this build** ---
not conditionally, not as a stretch goal. The product's value is:

``` text
Detect → Compare → Retrieve Policy → Reason → Prioritize → Explain → Human Decision
```

## Deterministic pre-processing (FFmpeg + OpenCV)

FFmpeg extracts 3--5 keyframes per clip at fixed timestamps. OpenCV is
used only for deterministic operations: HSV colour sampling in a tracked
region (as a corroborating, non-AI cross-check on Gemini's colour-change
claim), simple crop/mask for the compare view, and frame annotation. No
pretrained classifier, no `cv2.dnn`, no `cv2.face` --- enforced by a CI
grep gate (§29).

## Why frames, not raw video, go to Gemini

Paired reference/comparison keyframes plus the approved rule set are
sent in one structured-output call per pair. This is deterministic (same
frames → stable output), fast, cheap against the Google Cloud credit,
debuggable (a failure is traceable to one frame pair), and matches what
the Continuity Compare screen needs to render regardless.

No generative object replacement, inpainting, or video-generation model
is used anywhere in this build.

------------------------------------------------------------------------

# 12. Gemini Responsibilities

Two distinct roles, named distinctly so the specification does not
overclaim "agentic" behaviour where none exists:

**Analysis pipeline (deterministic sequence, not agentic):** 1. Extract
structured candidate policy rules with source quotes. 2. Compare paired
reference/comparison keyframes and emit a closed-enum `ai_assessment`
per tracked object. 3. Produce structured, schema-validated output for
both.

**SceneRights Agent (the one genuinely agentic surface --- ADK
orchestrator behind "Ask SceneRights"):** 1. Decide which tool a
question requires (ClickHouse MCP vs. stored policy context
vs. refusal). 2. Compose the read-only query. 3. Decide whether it has
enough retrieved state to answer, and say so explicitly when it does not
(never answers current-state questions from conversation memory). 4.
Explain a finding using retrieved observation + policy state.

Gemini does **not**: assign severity (derived deterministically from
matched-rule priority, §14), generate the production report
(deterministic template from rows), or run a second "QA" pass over its
own output. All three were removed from scope --- see §0 and §31.

------------------------------------------------------------------------

# 13. Example Gemini Output Contracts

## Policy extraction (per candidate rule)

``` json
{
  "policy_rule_id": "rule_001",
  "category": "continuity",
  "rule_text": "Lead actor wears a silver necklace throughout Scene 12.",
  "source_quote": "Lead actor wears a silver necklace throughout Scene 12.",
  "priority": "high",
  "scope": "scene_12"
}
```

## Continuity comparison (per tracked object, per frame pair)

``` json
{
  "object_type": "necklace",
  "object_label": "lead actor silver necklace",
  "reference": { "clip_id": "take_a", "ai_assessment": "present" },
  "comparison": { "clip_id": "take_b", "ai_assessment": "absent" },
  "model_assessment": "clear"
}
```

`model_assessment` is one of `clear`, `likely`, `uncertain` --- never a
percentage (see §24). Severity, policy citation, and `review_status` are
added by the backend after this response, not by Gemini.

------------------------------------------------------------------------

# 14. ClickHouse Data Model --- Authoritative Schema

This is the **only** schema in this document. It supersedes v6's §16 and
§38.

## projects (single seeded row for the hackathon build)

``` sql
CREATE TABLE IF NOT EXISTS projects
(
    project_id String,
    name String,
    status LowCardinality(String),
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id);
```

## policy_documents

``` sql
CREATE TABLE IF NOT EXISTS policy_documents
(
    project_id String,
    policy_id String,
    filename String,
    gcs_uri String,
    status LowCardinality(String),   -- 'uploaded'|'processing'|'ready'|'failed'
    created_at DateTime,
    updated_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, policy_id);
```

This table is intentionally minimal. It exists to persist the uploaded
policy workflow resource referenced by the `/policies/{policy_id}` API.
The parsed document body itself is not stored in ClickHouse.

## clips

``` sql
CREATE TABLE IF NOT EXISTS clips
(
    project_id String,
    clip_id String,
    scene_id String,
    role LowCardinality(String),   -- 'reference' | 'comparison'
    gcs_uri String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, clip_id);
```

## scenes

``` sql
CREATE TABLE IF NOT EXISTS scenes
(
    project_id String,
    scene_id String,
    name String,
    reference_clip_id String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id);
```

`reference_clip_id` is updated through the FastAPI application write path
when `/scenes/{scene_id}/reference` is called. For the single-scene demo,
this is the authoritative reference-selection state.

## policy_rules

``` sql
CREATE TABLE IF NOT EXISTS policy_rules
(
    project_id String,
    policy_id String,
    policy_rule_id String,
    document_name String,
    policy_type LowCardinality(String),
    rule_text String,
    source_quote String,
    priority LowCardinality(String),   -- 'high' | 'medium' | 'low'
    status LowCardinality(String),     -- 'extracted' | 'approved' | 'rejected'
    version UInt16,
    effective_date Nullable(DateTime),
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, policy_rule_id);
```

## analysis_runs

``` sql
CREATE TABLE IF NOT EXISTS analysis_runs
(
    project_id String,
    scene_id String,
    analysis_run_id String,
    status LowCardinality(String),   -- 'queued'|'running'|'succeeded'|'failed'
    step LowCardinality(String),
    error_code Nullable(String),
    started_at DateTime,
    completed_at Nullable(DateTime)
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, started_at);
```

## findings (append-only --- never mutated)

``` sql
CREATE TABLE IF NOT EXISTS findings
(
    project_id String,
    scene_id String,
    finding_id String,
    analysis_run_id String,
    finding_type LowCardinality(String),   -- 'continuity' | 'visual_review'
    object_type String,
    object_label String,
    reference_clip String,
    comparison_clip String,
    ai_assessment LowCardinality(String),  -- present|absent|not_visible|changed|uncertain
    model_assessment LowCardinality(String), -- clear|likely|uncertain
    severity LowCardinality(String),       -- derived from policy_rules.priority
    policy_rule_id String,
    policy_rule_version UInt16,
    policy_document String,
    policy_rule String,
    source_quote String,
    timestamp_ms UInt32,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, created_at);
```

## decisions (append-only --- the audit log)

``` sql
CREATE TABLE IF NOT EXISTS decisions
(
    project_id String,
    finding_id String,
    review_status LowCardinality(String), -- open|confirmed|not_issue|escalated|resolved
    previous_status LowCardinality(String),
    reviewer String,
    comment String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, finding_id, created_at);
```

## agent_runs

``` sql
CREATE TABLE IF NOT EXISTS agent_runs
(
    agent_run_id String,
    project_id String,
    scene_id String,
    request_type LowCardinality(String),
    tool_used LowCardinality(String),
    tool_status LowCardinality(String),
    row_count UInt32,
    started_at DateTime,
    completed_at Nullable(DateTime),
    error_code Nullable(String)
)
ENGINE = MergeTree
ORDER BY (project_id, started_at);
```

## findings_current (VIEW --- the state-mutation fix)

``` sql
CREATE VIEW IF NOT EXISTS findings_current AS
SELECT
    f.project_id,
    f.scene_id,
    f.finding_id,
    f.finding_type,
    f.severity,
    f.object_type,
    f.object_label,
    f.ai_assessment,
    f.policy_rule_id,
    f.policy_rule,
    f.source_quote,
    coalesce(d.review_status, 'open') AS review_status,
    d.reviewer AS last_reviewer,
    d.created_at AS decided_at
FROM findings AS f
LEFT JOIN
(
    SELECT
        project_id,
        finding_id,
        argMax(review_status, created_at) AS review_status,
        argMax(reviewer, created_at) AS reviewer,
        max(created_at) AS created_at
    FROM decisions
    GROUP BY project_id, finding_id
) AS d
    ON f.project_id = d.project_id
   AND f.finding_id = d.finding_id;
```

The agent and the `/findings` API both read `findings_current` only. A
human decision is a single `INSERT INTO decisions`; the next `SELECT`
against `findings_current` must reflect it without an `ALTER ... UPDATE`
mutation. `ST-STATE-01` verifies the end-to-end visibility target (\<2s)
on the deployed environment.

**Deliberately not built as ClickHouse tables for the hackathon:**
`organizations`, `users`, and `continuity_observations` as a table
distinct from `findings`. `policy_documents` and `scenes` are now included
because the P0 API contracts require persisted `policy_id` and
`reference_clip_id` state. Single-tenant demo scope still avoids full
organization/user entities; see §33 and §31.

------------------------------------------------------------------------

# 15. Agent + ClickHouse MCP Demo

``` text
User: "What unresolved issues remain in Scene 12?"
          ↓
Gemini Agent (ADK) decides: current-state question → MCP tool required
          ↓
official mcp-clickhouse (Streamable HTTP, read-only user, scoped view)
          ↓
SELECT ... FROM findings_current
WHERE project_id = {project_id} AND scene_id = 'scene_12'
  AND review_status IN ('open', 'escalated')
ORDER BY multiIf(severity='high',1,severity='medium',2,3), created_at ASC
          ↓
Gemini summarizes only the returned rows
          ↓
UI: answer + data-source chip + MCP Activity rail entry
```

The demo climax (§25) repeats this exact call after a human decision is
recorded, showing the same query returning fewer rows.

------------------------------------------------------------------------

# 16. Google Cloud Deployment

``` text
Frontend:        Next.js on Cloud Run
Backend:         FastAPI (Python 3.12) on Cloud Run
MCP server:      mcp-clickhouse as its own named Cloud Run service
                 (scenerights-mcp-clickhouse), Streamable HTTP transport,
                 bearer-token auth
AI:              Gemini via Vertex AI (google-genai / google-adk),
                 deployed through Google Cloud Agent Engine
Media:           Google Cloud Storage, signed URLs, 15-min TTL
Secrets:         Google Secret Manager, bound via --set-secrets at deploy
Observability:   Cloud Logging, structured, redacts document/prompt bodies
Partner:         ClickHouse Cloud + official mcp-clickhouse

Cloud Run config: min-instances=1 on frontend, backend, and MCP
service for the duration of the judging window (Sep 23 – Oct 7) to
avoid cold-start failures and idle-suspend issues.
```

------------------------------------------------------------------------

# 17. Accepted Google SDK Strategy

``` text
google-adk
google-genai
```

Both are on the rules' accepted-package list, alongside
`google-generativeai` and `google-cloud-aiplatform` (any generation).
The agent is built with `google-adk` and deployed via **Google Cloud
Agent Engine**, matching the rules' "What to Create" language ("powered
by Gemini and Google Cloud Agent Builder") explicitly rather than only
implicitly through the SDK choice. This is stated plainly in the README
and submission text, and the Agent Engine deployment step is documented
in `docs/architecture.md`.

------------------------------------------------------------------------

# 18. Repository Requirements

``` text
PUBLIC
OPEN SOURCE — Apache-2.0, license file detectable in repo About section
NEW FOR THIS CONTEST — fresh git init, first commit inside the contest
  period, no code imported from any prior SceneRights document/repo
RUNNABLE
DOCUMENTED
```

Include: `README.md`, `LICENSE`, frontend source, backend source, ADK
agent code/config, `mcp-clickhouse` deployment config, deployment
instructions, the fictional sample policy, the three original demo
clips, `.env.example`, `docs/architecture.md`, `docs/clickhouse-mcp.md`,
`prompts/` (see §19). No secrets. A one-line statement in the README:
*"This repository was created for the Agentic Cinema Hackathon and
contains no code predating the contest period."*

------------------------------------------------------------------------

# 19. Repository Structure

``` text
scenerights-ai/
├── apps/
│   └── web/
├── services/
│   ├── api/
│   └── mcp-clickhouse/          # deployment config for the partner MCP server
├── agents/
│   └── supervisor/
├── tools/
│   ├── video/
│   └── clickhouse/
├── prompts/
│   ├── policy_extraction.md
│   ├── continuity_compare.md
│   └── agent_system.md
├── database/
│   └── clickhouse/               # DDL from §14
├── samples/
│   ├── fictional-policy/
│   └── original-demo-footage/
├── docs/
│   ├── architecture.md
│   ├── compliance.md
│   ├── clickhouse-mcp.md
│   ├── demo-script.md
│   └── testing.md
├── .env.example
├── LICENSE
└── README.md
```

------------------------------------------------------------------------

# 20. Competition Submission Requirements Checklist

## Project

-   [ ] Newly created during contest period; fresh repo history.
-   [ ] Team ≤ 4 eligible individuals; Representative designated if a
    team.
-   [ ] Functional AI agent, Gemini + Google Cloud Agent Engine.
-   [ ] Selected Partner (ClickHouse) technology used at runtime.
-   [ ] Runs on web.

## AI Compliance

-   [ ] No OpenAI / Anthropic / AWS AI / Microsoft AI in the runtime.
-   [ ] No unauthorized agent frameworks.
-   [ ] CI dependency/compliance gate passes (§29).

## ClickHouse Track

-   [ ] Official `mcp-clickhouse` used, Streamable HTTP, connected at
    runtime.
-   [ ] Gemini agent visibly invokes MCP (data-source chip + Activity
    rail).
-   [ ] chDB tools disabled; tool_filter restricts to read-only tools.

## Repository

-   [ ] Public, Apache-2.0 license visible in repo About section.
-   [ ] Google + Partner integration imported and actually called (not
    just named).
-   [ ] Google Cloud credit request form submitted by Aug 31, 2026.

## Hosted Product

-   [ ] Public judging URL, `min-instances=1` through Oct 7.
-   [ ] Demo-access token gates the shared instance (§33) --- no
    login/signup.

## Demo Video

-   [ ] ≤ 3 minutes, public YouTube/Vimeo, English.
-   [ ] No real vehicle/license plate; no third-party brands in frame.
-   [ ] On-camera performer is a team member (no third-party publicity
    exposure).

## Submission Text

-   [ ] Feature summary, technologies used, findings/learnings,
    including the append-only ClickHouse design as a specific technical
    callout.

------------------------------------------------------------------------

# 21. Stage One Pass/Fail Strategy

``` text
Does the app run from a clean browser session?
Does Gemini run (visible in agent_runs)?
Does Google Cloud Agent Engine run?
Does official mcp-clickhouse run (visible in its own Cloud Run service)?
Is the demo-access token documented for judges?
Does the repo contain setup instructions and a license?
Does the video show the real hosted app?
```

------------------------------------------------------------------------

# 22. Stage Two Strategy

Equally weighted: Technological Implementation, Design, Potential
Impact, Quality of the Idea. The append-only ClickHouse design and the
MCP Activity rail are the two strongest, cheapest levers for
Technological Implementation. The reworked dashboard hero (§30) is the
strongest lever for Design. The three real success metrics (§32) are the
strongest lever for Potential Impact.

------------------------------------------------------------------------

# 23. Demo Dashboard

``` text
PROJECT: Scene 12 (Northstar Studios)

[ Take A ]  ↔  [ Take B ]        <- hero: side-by-side takes, top of page
Necklace: ⚠ absent   Mug: ⚠ changed

POLICY:  3 rules active (1 pending approval)
FINDINGS: 2 open, 1 resolved
AGENT: 12 MCP queries this session

ASK SCENERIGHTS
"What needs attention before picture lock?"
```

The count-card grid from v6 (Active Policies / Open Findings /
Continuity / Privacy / Brand / Resolved) is demoted below the fold ---
it doesn't communicate the product in ten seconds, and NFR-009 requires
that it does.

------------------------------------------------------------------------

# 24. Three-Minute Demo Script (single authoritative version)

Replaces all three competing v6 scripts.

  -----------------------------------------------------------------------
  Time                    Beat                    What's shown
  ----------------------- ----------------------- -----------------------
  0:00--0:10              Hook                    Take A / Take B side by
                                                  side, full-bleed, no
                                                  chrome. VO: "Same
                                                  scene, two takes ---
                                                  one of these costs you
                                                  a reshoot."

  0:10--0:20              Grounding setup         Cut to Screen C: three
                                                  approved rules
                                                  extracted from the
                                                  studio's own uploaded
                                                  policy, human-approved.

  0:20--0:35              Analysis                Processing stepper,
                                                  then findings surface.

  0:35--1:10              **Grounding beat**      Continuity Compare:
                                                  necklace ⚠, mug ⚠. Open
                                                  the necklace finding
                                                  --- policy source panel
                                                  shows the *exact
                                                  clause*, with
                                                  `source_quote`
                                                  highlighted.

  1:10--1:30              **Credibility beat**    Take C (occlusion).
                                                  System reports "not
                                                  visible --- cannot
                                                  determine," not
                                                  "missing." VO: "It
                                                  won't guess."

  1:30--2:05              **Partner beat**        Ask SceneRights:
                                                  "What's unresolved in
                                                  Scene 12?" MCP Activity
                                                  rail lights up: tool,
                                                  SQL, row count,
                                                  latency. Answer read
                                                  aloud.

  2:05--2:35              **Climax**              Reviewer confirms +
                                                  resolves the necklace
                                                  finding. Same question
                                                  asked again.
                                                  Split-screen:
                                                  before/after answers
                                                  shown simultaneously.

  2:35--2:50              Close the loop          Dashboard:
                                                  open-findings count
                                                  drops; `agent_runs`
                                                  counter visible.

  2:50--3:00              Vision                  One sentence. Hard cut
                                                  at 3:00.
  -----------------------------------------------------------------------

Record risky live-Gemini beats (0:20--0:35, 1:30--2:35) separately from
a clean take of the rest, so a single slow API response doesn't cost a
full re-record.

------------------------------------------------------------------------

# 25. What Not to Build

``` text
feature-length processing
logo/object localisation bounding boxes
professional VFX / generative repair (not conditional — not built at all)
real trademark/legal determination
3D/VR support
mobile apps
large multi-agent hierarchy
dozens of policy types
policy scope hierarchy / precedence / conflict detection
policy versioning UI
earring / jewelry-style/colour detection
license plate detection
Scene Workspace screen / timeline / shot-strip UI
login, signup, multi-user accounts
```

A reliable narrow workflow scores better than an unfinished platform.
Full list of deferred scope, with reasons, is in §31.

------------------------------------------------------------------------

# 26. Delivery Schedule

18 days remain from the audit date to the deadline (Sep 9, 2:00 PM PT).
This schedule targets submission one day early.

  -----------------------------------------------------------------------
  Date                    Milestone               Exit criteria
  ----------------------- ----------------------- -----------------------
  Day 0--1 (immediate)    Google Cloud \$100      Confirmation received
                          credit form submitted   
                          (deadline Aug 31)       

  Day 1--3                Shoot Takes A, B, C     Three usable original
                                                  clips, ≥1080p, matched
                                                  lighting

  Day 1--4                Backend skeleton +      §14 schema live;
                          ClickHouse              project/clip/policy
                                                  upload work end to end

  Day 4--7                Policy pipeline         Extraction +
                                                  source_quote
                                                  validation + approval
                                                  UI working

  Day 5--9                Continuity pipeline     FFmpeg keyframes →
                                                  Gemini paired-frame
                                                  comparison → findings
                                                  written

  Day 9--12               Agent + MCP             ADK agent,
                                                  `mcp-clickhouse`
                                                  deployed as its own
                                                  service, read-only
                                                  enforced, Activity rail
                                                  rendering

  Day 10--14              Frontend                Dashboard hero,
                                                  Continuity Compare,
                                                  Findings Queue, Policy
                                                  Rule Review, Ask
                                                  SceneRights

  Day 14--16              Demo rehearsal          Full run 5× on the
                                                  deployed URL; AI-CON-04
                                                  (identical takes → zero
                                                  findings) passing

  Day 16--17              Video shoot + edit      ≤3 min, uploaded to
                                                  YouTube/Vimeo, public

  Day 17                  Submission              All Stage One checklist
                                                  items pass

  Day 18 (buffer)         ---                     Unused if on schedule;
                                                  absorbs slippage

  Sep 23 -- Oct 7         Judging window          `min-instances=1`
                                                  maintained; weekly
                                                  health check that the
                                                  hosted URL and
                                                  Gemini/ClickHouse quota
                                                  are still live
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 27. Definition of Done

``` text
[ ] Company policy uploads; Gemini extracts rules with validated source_quote.
[ ] Human approves rules.
[ ] Three original clips upload; Take A set as reference.
[ ] Gemini reliably identifies the necklace and mug differences on
    paired keyframes.
[ ] Occlusion take reports not_visible, never absent.
[ ] Findings cite the applicable approved policy rule and source_quote.
[ ] Findings persist append-only in ClickHouse; findings_current view
    reflects human decisions with no mutation delay.
[ ] Gemini agent retrieves current state through official
    mcp-clickhouse (Streamable HTTP, read-only grant, scoped views).
[ ] Human resolves a finding; the next agent query reflects it in the
    same session, verified by ST-STATE-01 (<2s).
[ ] App deployed on Cloud Run, min-instances=1, publicly testable with
    the documented demo-access token — no login/signup.
[ ] Repository is public, Apache-2.0 licensed, fresh history inside
    the contest period.
[ ] CI compliance gate passes: no prohibited AI dependency, no cv2.dnn,
    no committed secrets (gitleaks).
[ ] Demo uses only original/authorized material; no license plate, no
    third-party brand in frame.
[ ] Full demo completes in under three minutes.
[ ] AI-CON-04 (identical takes → zero findings) passes.
```

------------------------------------------------------------------------

# 28. MVP Priority Matrix (by Functional Requirement ID)

## P0 --- Must Build

``` text
FR-001  Create project (single seeded project; no create UI needed)
FR-003  Enforce authorization for project resources (token-scoped, §33)
FR-004  Upload supported policy files
FR-005  Store policy files privately
FR-007  Gemini generates structured candidate rules
FR-008  Candidate rules require human approval
FR-009  Rules retain source attribution (source_quote, validated)
FR-015  Upload supported video clips
FR-016  Store uploaded media privately
FR-019  Create continuity scenes
FR-021  Designate reference take
FR-024  Gemini compares reference/comparison paired frames
FR-025  Distinguish absent/not_visible/uncertain
FR-026  Detect mug colour difference
FR-027  Detect necklace presence difference
FR-028  Findings created only after schema validation
FR-031  Policy-grounded findings cite source
FR-034  Confirm a finding
FR-037  Resolve a finding
FR-039  Route current-state questions to ClickHouse MCP
FR-044  Findings persist in ClickHouse (append-only)
FR-047  Official ClickHouse MCP used at runtime
FR-048  At least one demo workflow visibly depends on MCP-retrieved data
FR-053  Async analysis exposes a pollable run status (new, §39)
```

## P1 --- Build If Time

``` text
FR-006  Extract policy text (beyond the single-doc happy path)
FR-032  "No applicable policy" explicit statement
FR-033  Findings include severity/status/explanation in full detail
FR-035  Mark finding not-an-issue
FR-038  Decision audit trail UI
FR-040  Agent failure handling (MCP unavailable → explicit statement)
FR-041  Agent explains findings using stored state
FR-049  Production report (deterministic template)
Fictional-logo visual-review detection
```

## P2 --- Post-Hackathon (see §31 for full list and rationale)

``` text
FR-002, FR-010, FR-011, FR-012, FR-013, FR-014, FR-018, FR-020,
FR-022, FR-023, FR-036, FR-042, FR-043, FR-045, FR-046, FR-050
```

------------------------------------------------------------------------

# 29. AI Coding Agent Instructions

``` text
1. Do not replace Google ADK/Gemini with another AI provider.
2. Do not add external AI models or LangChain/CrewAI/AutoGen.
3. Do not build any generative video/image repair or replacement.
4. Do not bypass official ClickHouse MCP for the required agent
   runtime demo; do not give the MCP database user write access.
5. Do not enable chDB tools; restrict the agent's tool_filter to
   run_select_query and list_tables only.
6. Do not implement login/signup — this build uses a single seeded
   project and a shared demo-access token, scoped server-side.
7. Do not mutate the findings table. All state changes are inserts
   into decisions; current state is read from findings_current.
8. Do not have Gemini assign severity, write the production report, or
   run a self-QA pass on its own output.
9. Do not treat not-visible as missing.
10. Do not make AI findings final without human review.
11. Do not use cv2.dnn, cv2.CascadeClassifier, or any pretrained
    OpenCV classifier — deterministic transforms only.
12. Do not expose secrets, credentials, or raw SQL connection strings
    to the frontend or in logs.
13. Do not use real third-party brands, vehicles, or license plates in
    demo assets.
14. Prioritize P0 (§28) and the acceptance tests in §37/§40 before any
    P1/P2 item.
15. If a requirement is technically blocked, report the blocker before
    silently changing scope.

CI gate (run on every commit):
  1. Dependency allowlist / lockfile inspection (PRIMARY):
     - Python runtime dependencies must match the reviewed allowlist.
     - Node runtime dependencies must match the reviewed allowlist.
     - Fail if a prohibited AI provider SDK, inference client, embedding
       package, or agent framework is introduced.
  2. Runtime import/config scan (ENFORCING):
     - Fail on actual imports/configuration for prohibited AI providers or
       agent frameworks in services/, apps/, agents/, or tools/.
     - Do not fail merely because a provider name appears in comments,
       documentation, tests, or defensive validation text.
  3. Deterministic OpenCV scan (ENFORCING):
     grep -rE "cv2\.dnn|cv2\.CascadeClassifier|cv2\.face" tools/
       → fail the build if any match is found.
  4. Secret scan (ENFORCING):
     gitleaks detect → fail on any secret match.
  5. Produce a CI compliance summary artifact listing reviewed runtime
     dependencies and the checks above for submission evidence.
```

------------------------------------------------------------------------

# 30. UI Design System

## Product Style

**Cinematic Production Control Room.** Dark, dense but readable,
professional, production-focused, minimal decoration, strong status
hierarchy, subtle motion only. Not a generic consumer AI chatbot.

## Color Tokens

``` text
background.primary   #090A0C      accent.primary        #E3A544
background.secondary #111318      accent.primary.hover   #F0B65B
panel                 #15181D     status.critical        #D9544D
panel.hover            #1B1F25    status.warning         #D89B3C
border                 #262B33    status.success         #5EA876
text.primary            #F5F7FA   status.info             #5F8EC9
text.secondary          #A5ACB8
text.muted               #707782
```

## Typography

Geist, fallback Inter/system sans-serif. Page Title 24--28px semibold,
Section Title 18--20px semibold, Card Title 14--16px semibold, Body
14px, Metadata 12px.

## Shape

Border radius 8--12px, 1px subtle borders, minimal shadows, compact
professional spacing. Avoid heavy gradients, glow effects,
glassmorphism, pill UI, conversational chat bubbles, decorative
animation.

## Component Inventory (14 --- cut from v6's 27)

``` text
AppShell
TopBar
ProjectSidebar
VideoPlayer
FindingCard
FindingTable
PolicySourceCard
PolicyRuleCard
ContinuityCompare
AgentPanel
McpActivityRail          <- new
StatusBadge
SeverityBadge
AsyncBoundary             <- replaces separate Loading/Empty/Error states
```

Cut and why: `BoundingBoxOverlay` (unreliable small-object localisation,
risk of a visibly wrong box on stage), `FrameScrubber` (native `<video>`
controls suffice), `ConfidenceMeter` (§24 --- no percentage is shown),
`IssueMarker`/timeline (requires the Scene Workspace screen, cut --- see
§31), `ReportPanel` (P1).

## Screens (5 --- cut from v6's 7)

**Screen A --- Dashboard.** Reworked hero per §23. P0. **Screen B ---
Policy Rule Review.** Extracted rule, source_quote shown inline,
Approve/Reject. P0. **Screen C --- Continuity Compare.**
Reference/comparison side by side, tracked-object list with ✓/⚠, matched
policy rule, model_assessment (enum, not %), Confirm/Not an
Issue/Escalate actions. P0 --- the hero screen. **Screen D --- Findings
Queue.** Priority/scene/type/object/status table. P0. **Screen E --- Ask
SceneRights.** Constrained side panel with the MCP Activity rail. P0.

Cut: Policy Library (P1 --- the demo shows one policy, a list view adds
nothing), Scene Workspace (P2 --- Continuity Compare covers the demo
need without the three-panel/bounding-box/frame-navigation cost).

## UX States

Every async surface uses the single `AsyncBoundary` component: idle →
loading → success → empty → partial → failed. Never a blank panel while
processing.

------------------------------------------------------------------------

# 31. Post-Hackathon Roadmap

Everything below was in v6's P0/general scope and is deliberately
deferred, not abandoned. Kept here so the full product vision remains
visible to reviewers and to future-us.

**Policy intelligence** - Multi-level policy scope
(organization/client/project/scene) with explicit precedence rules (v6
UC-005, FR-010). - Policy versioning and disable/reactivate workflow (v6
UC-006, FR-012). - Policy conflict detection across two active approved
policies (v6 UC-025, FR-013). - Edit-then-approve on extracted rules,
storing both `extracted_text` and `approved_text` distinctly.

**Continuity / visual review** - Earring presence/appearance detection
(high false-positive risk without controlled framing). - Jewelry
colour/style change detection (metal appearance is
white-balance-dominated; needs a controlled lighting rig to be
reliable). - Wardrobe and hair/makeup continuity. - Object
position/orientation and food/drink-level tracking. - Readable license
plate / privacy-sensitive-element detection --- **cut for compliance
risk** (real vehicle = manufacturer trademark + arguable third-party PII
under the video rules), not only feasibility. Revisit only with a fully
fictional, non-trademarked prop plate design. - Bounding-box overlays on
the video viewer, once a reliable small-object localisation approach is
validated. - Multi-take (\>2) scenes.

**Platform** - Real multi-tenant authentication (Firebase / Google
Identity Platform), replacing the single-token demo-mode scoping in
§33. - Multiple organizations/projects, with `organizations` and `users`
as real ClickHouse (or Firestore) tables and ClickHouse row policies for
tenant isolation at the database layer. - Full audit-history UI beyond
the raw decisions log. - Report export (PDF/DOCX) beyond the in-app
deterministic template. - Timeline/shot-strip UI, frame-accurate issue
markers. - Scene Workspace three-panel view with frame navigation. -
Generative visual repair --- **only** if using a competition-permitted
Google Cloud AI capability at that time; still out of scope for the
hackathon build entirely. - NLE (editing suite) integration. - Advanced
analytics / feature-length processing / multi-studio enterprise
controls.

------------------------------------------------------------------------

# 32. Product Requirements Document (PRD)

## Product Name

**SceneRights AI**

## Product Vision

SceneRights AI is a Gemini-powered production supervisor that helps
filmmakers and studio teams review footage against their own approved
production policies, identify cross-shot continuity issues, preserve an
auditable history of findings and decisions, and query current
production state through an agentic interface backed by ClickHouse.

## Problem Statement

Production teams can miss small visual details that later create
editing, continuity, or clearance problems: a necklace disappears
between takes; a hero prop changes colour; an unintended element appears
in frame; a reviewer cannot easily determine which findings remain
unresolved. Manual review is repetitive and depends on human memory.
SceneRights provides an AI-assisted first review while keeping final
decisions with authorized production staff.

## Primary Users (2, for the hackathon build)

**Script Supervisor** --- sets the continuity reference, reviews
continuity findings. **Reviewer** --- confirms, escalates, or resolves
findings; approves extracted policy rules.

Production Manager, Brand/Clearance Reviewer, and Studio Administrator
remain named personas for the product vision but are not designed for in
the hackathon UI --- see §31.

## Product Goals

``` text
G-01 Reduce manual continuity-review effort.
G-02 Ground visual findings in studio/project policies.
G-03 Make uncertainty explicit instead of inventing certainty.
G-04 Preserve human approval for consequential decisions.
G-05 Provide auditable production-state history.
G-06 Demonstrate meaningful Gemini + Google Cloud + ClickHouse MCP
     runtime integration.
G-07 Deliver a clear three-minute hackathon demo.
```

## Non-Goals for Hackathon MVP

``` text
NG-01 Feature-length automated film review.
NG-02 Legal advice or final trademark/copyright determinations.
NG-03 Fully automated professional VFX replacement.
NG-04 Perfect identity tracking across arbitrary films.
NG-05 General-purpose filmmaking chatbot.
NG-06 3D/VR conversion.
NG-07 Automatic destructive database administration.
NG-08 Multi-user accounts, login, or signup.
```

## MVP Success Metrics

``` text
SM-01 One policy file uploads and processes.
SM-02 Exactly three structured rules are extracted from the demo
      policy (matches §7 fictional policy exactly).
SM-03 A human approves/rejects extracted rules.
SM-04 Three original clips upload and link (A/B/C).
SM-05 Take A is designated reference.
SM-06 The system identifies both planted continuity differences
      (necklace, mug) and correctly reports the occlusion case as
      not_visible.
SM-07 Findings cite applicable approved policy rules with a validated
      source_quote.
SM-08 Findings persist append-only in ClickHouse.
SM-09 Gemini queries unresolved state through official ClickHouse MCP.
SM-10 A human decision (INSERT into decisions) changes the derived
      state in findings_current.
SM-11 A second agent query reflects the changed state within the same
      session, in under 2 seconds.
SM-12 The complete demo fits within three minutes.
SM-13 Zero false positives when Take A is compared against itself
      (AI-CON-04).
SM-14 100% of the occlusion case is classified not_visible, never
      absent.
SM-15 Every finding either cites an approved rule ID + validated
      source_quote, or is explicitly labelled "no matching policy" —
      zero ungrounded findings.
```

------------------------------------------------------------------------

# 33. Actors and Permissions

Simplified for the no-login demo build:

  -----------------------------------------------------------------------
  Actor                               Permissions
  ----------------------------------- -----------------------------------
  Demo user (single shared role,      Upload policy/media, approve rules,
  gated by the demo-access token)     review/resolve findings, ask the
                                      agent

  SceneRights Agent                   Read approved policy/state via MCP;
                                      retrieve and explain; no
                                      independent final approval, no
                                      write access
  -----------------------------------------------------------------------

The full org-admin/project-admin/reviewer/script-supervisor/viewer model
from v6 (§56) is preserved as the target permission model for the
post-hackathon multi-tenant build (§31) but is not implemented for the
hackathon demo, which runs as a single scoped project behind one shared
token.

**Security positioning:** the shared demo-access token is a
hackathon-only access-control mechanism. It is not production-grade
authentication and must not be described in the README, demo, or
submission as enterprise multi-tenant security. Production identity,
per-user authorization, and tenant isolation remain post-hackathon scope
(§31).

------------------------------------------------------------------------

# 34. Use Case Catalogue (P0 --- 12 core use cases)

## UC-001 Upload Company Policy

**Actor:** Demo user. **Precondition:** valid demo-access token. **Main
flow:** upload PDF/DOCX/TXT/Markdown → stored privately → processing
status `processing` → extraction starts. **Failures:** unsupported file,
file too large, empty file, parsing failure, storage failure --- all
show a clear, recoverable error. **Postcondition:** policy document
record exists with `status=processing`.

## UC-002 Extract Structured Policy Rules

**Actor:** Analysis pipeline (not "agent" --- see §12). Extracts
candidate rules, each with `policy_rule_id`, `category`, `rule_text`,
`source_quote`, `priority`. `source_quote` is validated as an exact
substring of the parsed document text; failing rules are auto-rejected
before reaching the approval queue. Rules are never marked enforced
before human approval.

## UC-003 Approve / Reject Extracted Rule

**Actor:** Demo user. Approve or Reject. Only approved rules are used as
authoritative policy for new findings.

## UC-004 Upload Video Clip

**Actor:** Demo user. Upload original/authorized video; backend
validates type/size/duration (max 100MB, max 60s); media stored
privately; clip record created; processing state visible.

## UC-005 Create Continuity Scene and Select Reference Take

**Actor:** Demo user. Groups Take A/B(/C) under a scene; marks one take
as reference.

## UC-006 Compare Reference and Comparison Takes

**Actor:** Analysis pipeline. FFmpeg extracts paired keyframes; Gemini
emits `ai_assessment` per tracked object from a closed enum:
`present | absent | not_visible | changed | uncertain`. Occluded regions
resolve to `not_visible`, never `absent`.

## UC-007 Detect Missing Necklace

Reference shows necklace clearly; comparison area is clearly visible but
the necklace is not detected → `ai_assessment=absent`, surfaced as a
finding requiring human review. Never claimed with absolute certainty.

## UC-008 Detect Hero Prop Colour Change

Reference: blue mug. Comparison: red mug → `ai_assessment=changed`.
Primary demo capability --- most visually reliable detection in scope.

## UC-009 Handle Occlusion

Reference necklace is visible; comparison neck region is substantially
covered → `ai_assessment=not_visible`. Explicitly not converted to
`absent`. Not raised as an actionable finding --- surfaced as a system
capability in the demo.

## UC-010 Match Observation to Policy and Explain Finding

The pipeline/agent retrieves the small approved rule set (passed
directly in context --- see §11, no retrieval subsystem needed at this
scale) and separates Observation / Policy / Interpretation /
Recommendation. If no rule matches: "No applicable approved company
policy found."

## UC-011 Review and Resolve Finding

**Actor:** Demo user. Actions: Confirm, Not an Issue, Escalate, Resolve.
Every action is a single `INSERT INTO decisions` (§14) --- an audit
record by construction, no separate audit mechanism needed.

## UC-012 Query Unresolved Findings Through Agent

**Actor:** Demo user, via the SceneRights Agent. "What unresolved issues
remain in Scene 12?" → agent decides MCP is required → queries
`findings_current` via official ClickHouse MCP → summarizes only
returned rows. This is the mandatory hackathon demo interaction (§15,
§24).

------------------------------------------------------------------------

**Prompt-injection handling (applies across UC-001, UC-004, UC-006,
UC-012):** uploaded policy text and any text visible inside uploaded
video frames are both treated as untrusted data, never as instructions,
enforced structurally by (a) passing all untrusted content as a
distinct, delimited content part, never concatenated into the
instruction, and (b) constraining every AI output to a fixed JSON schema
with no field capable of expressing an instruction override. The
human-approval gate (UC-003) is the final backstop even if the first two
were somehow bypassed.

**Failure use cases (all P0-adjacent, cheap, and already well specified
in v6 --- kept verbatim in spirit):** - Video processing failure →
`analysis_run.status=failed`, clear error, retry option, no fabricated
findings. - Gemini structured-output failure → schema validation fails,
bounded retry, then `failed`/`partial` --- no invalid finding persisted
as confirmed. - ClickHouse MCP unavailable → the agent explicitly
reports that current project state could not be retrieved; it never
answers from conversation memory.

------------------------------------------------------------------------

# 35. Non-Functional Requirements

## Performance

``` text
NFR-001 UI interactions not requiring AI respond within 500ms
        (excluding network variability).
NFR-002 Upload progress is visible.
NFR-003 Long-running analysis exposes progress/status via
        GET /api/analysis/{id} rather than blocking the UI.
NFR-019 Policy extraction completes in ≤45s (p95) for a ≤2-page document.
NFR-020 Two-take scene analysis completes in ≤90s (p95) for ≤20s clips.
NFR-021 Agent MCP-backed answer returns in ≤8s end-to-end (p95).
NFR-022 Hosted app serves first meaningful paint in ≤5s from cold
        start (min-instances=1 during the judging window).
```

## Reliability

``` text
NFR-005 Failed AI calls never create fabricated successful results.
NFR-006 Failed media processing is retryable.
NFR-007 POST /analyze accepts an Idempotency-Key header; a repeated
        analyze on an unchanged (scene_id, reference_clip_id,
        comparison_clip_id) returns the existing analysis_run_id
        rather than starting a new run and duplicating findings.
NFR-008 Human decisions are never lost on UI refresh (persisted via
        the decisions insert immediately on click).
```

## Usability

``` text
NFR-009 A judge understands the core product purpose within ~10
        seconds (served by the reworked dashboard hero, §23).
NFR-010 Critical findings are visually distinguishable from
        informational states (severity badge, not colour alone).
NFR-011 Policy source is reachable from a finding in one interaction.
NFR-012 The agent panel remains secondary to the production workspace.
```

## Accessibility

``` text
NFR-013 Core controls are keyboard reachable where practical.
NFR-014 Status never relies on colour alone (icon + label).
NFR-015 Text/background contrast meets WCAG AA for primary content.
```

## Maintainability / Observability / Availability

``` text
NFR-016 AI provider usage is isolated behind Google-specific service
        modules.
NFR-017 MCP configuration is documented in docs/clickhouse-mcp.md.
NFR-018 Environment-specific secrets are never hard-coded; bound via
        Secret Manager at deploy.
NFR-023 Every agent tool invocation results in one agent_runs row
        (tool name, status, row count, latency), written by the FastAPI/ADK
        orchestration layer through the application write connection after
        the MCP call returns; the MCP service itself remains read-only.
NFR-024 The hosted URL responds 200 for the entire judging window
        (Sep 23 – Oct 7); verified by a weekly manual check (§26).
```

------------------------------------------------------------------------

# 36. AI and Agent Requirements

``` text
AIR-001 Only competition-permitted Google Cloud AI and partner AI
        features are used in the submitted project (enforced by the CI
        dependency/compliance gate, §29).
AIR-002 All Gemini output is structured and validated by
        Pydantic/JSON schema.
AIR-003 Observation is always represented separately from policy
        interpretation.
AIR-004 Uncertainty is expressed via model_assessment
        (clear/likely/uncertain), never a percentage.
AIR-005 Gemini never invents company policy; source_quote validation
        (§9) enforces this structurally, not just by instruction.
AIR-006 Gemini never claims legal certainty.
AIR-007 Uploaded documents AND video content are data, not
        instructions — enforced structurally (§34).
AIR-008 Current-state questions requiring database truth invoke
        ClickHouse MCP; the agent never answers such questions from
        conversation memory.
AIR-009 Tool failures are surfaced to the user, never hidden or
        silently retried into a fabricated answer.
AIR-010 Every tool invocation is recorded in agent_runs for
        debugging/demo verification.
AIR-011 Human approval is required for extracted policy rules.
AIR-012 Human approval is required for every finding's final
        disposition.
```

------------------------------------------------------------------------

# 37. Security and Privacy Requirements

``` text
SEC-001 Policy documents are private by default (signed URLs, 15-min TTL).
SEC-002 Video files are private by default (signed URLs, 15-min TTL).
SEC-004 Backend APIs verify the demo-access token on every request.
SEC-005 ClickHouse credentials never reach frontend clients.
SEC-006 Production secrets use Secret Manager, bound via --set-secrets.
SEC-007 The MCP ClickHouse user (scenerights_mcp_ro) has SELECT-only
        grant on pre-filtered views, not base tables; no
        INSERT/ALTER/DROP grant exists at the database level.
SEC-008 End-user prompts never become arbitrary SQL — the agent's tool
        surface is restricted to run_select_query and list_tables via
        ADK tool_filter; chDB tools are disabled entirely
        (CHDB_ENABLED=false).
SEC-009 readonly=1 is enforced in the ClickHouse user's profile
        settings, not only as a query-level flag —
        CLICKHOUSE_ALLOW_WRITE_ACCESS=false and
        CLICKHOUSE_ALLOW_DROP=false are both set explicitly.
SEC-010 Uploaded policy content and video content are both protected
        against prompt-injection influence (§34).
SEC-011 Logs redact document/prompt bodies by default.
SEC-012 Public repository samples are fictional/original only.
SEC-013 Real confidential company policies are never committed.
SEC-014 The decisions table is itself the audit record — reviewer and
        timestamp on every row, by construction.
SEC-015 Rate limiting on POST /api/agent/query (per-token token
        bucket) to bound Gemini spend against the shared demo token.
```

------------------------------------------------------------------------

# 38. Data Requirements and State Machines

## Minimum Entities (ClickHouse --- see §14 for full DDL)

``` text
Project (single seeded row)
PolicyDocument
PolicyRule
Scene
Clip
AnalysisRun
Finding
Decision
AgentRun
```

## Policy Rule State Machine

``` text
extracted → approved
extracted → rejected
```

(Version/inactive states deferred --- §31.)

## Finding State Machine (review_status, written only via decisions inserts)

``` text
open → confirmed → resolved
open → not_issue
open → escalated
```

`ai_assessment` (present/absent/not_visible/changed/uncertain) is
written once by the pipeline and never changes; `review_status` is
derived from the `decisions` append-log via `findings_current`.
Transitions are validated server-side before the insert is accepted.

------------------------------------------------------------------------

# 39. Backend API Contracts

All project-scoped resources are nested under
`/api/projects/{project_id}/...`. Every request is validated against the
demo-access token server-side (SEC-004).

**Identifier contract:** `policy_id` identifies the uploaded policy
document/workflow resource used by policy endpoints; `policy_rule_id`
identifies one extracted rule and is the identifier persisted with
findings. Before frontend integration begins, endpoint DTOs, Pydantic
schemas, ClickHouse columns, TypeScript types, and UI enums must be
checked against the authoritative vocabulary in §§13--14 and §38. No
alias such as `rule_id` may be introduced.

## Write endpoints

``` text
POST /api/projects/{project_id}/policies                       Upload policy
POST /api/projects/{project_id}/policies/{policy_id}/process   Run extraction
POST /api/projects/{project_id}/policies/{policy_id}/rules/{policy_rule_id}/approve
POST /api/projects/{project_id}/policies/{policy_id}/rules/{policy_rule_id}/reject
POST /api/projects/{project_id}/clips                          Upload clip
POST /api/projects/{project_id}/scenes                         Create scene
POST /api/projects/{project_id}/scenes/{scene_id}/reference    Set reference clip
POST /api/projects/{project_id}/scenes/{scene_id}/analyze      202 -> {analysis_run_id, status:"queued"}
POST /api/projects/{project_id}/findings/{finding_id}/decision Record human decision (INSERT into decisions)
POST /api/projects/{project_id}/agent/query                    Ask SceneRights
POST /api/projects/{project_id}/seed                           Demo-only: reset to seeded state
```

## Read endpoints

``` text
GET /api/projects/{project_id}
GET /api/projects/{project_id}/policies
GET /api/projects/{project_id}/policies/{policy_id}/rules
GET /api/projects/{project_id}/clips
GET /api/projects/{project_id}/scenes/{scene_id}
GET /api/projects/{project_id}/analysis/{analysis_run_id}   Poll job status
GET /api/projects/{project_id}/scenes/{scene_id}/findings   Reads findings_current
GET /api/projects/{project_id}/findings/{finding_id}
GET /api/projects/{project_id}/findings/{finding_id}/history  Reads decisions
GET /api/projects/{project_id}/report                       Deterministic template
GET /healthz                                                 Liveness (app + MCP)
```

## Agent query

Request:

``` json
{ "project_id": "project_001", "scene_id": "scene_12",
  "message": "What unresolved issues remain?" }
```

Response:

``` json
{
  "answer": "Scene 12 has two unresolved findings.",
  "tool_calls": [
    { "tool": "clickhouse_mcp", "sql_summary": "SELECT ... FROM findings_current WHERE ...",
      "row_count": 2, "latency_ms": 340, "status": "success" }
  ]
}
```

Raw credentials and connection strings are never included; the
formatted, read-only SQL summary is shown deliberately (§15) to make the
integration visible to judges.

## Error envelope (uniform across all endpoints)

``` json
{ "error": { "code": "MCP_UNAVAILABLE", "message": "...",
             "retryable": true, "details": {} } }
```

Code list: `UPLOAD_FAILED`, `PARSE_FAILED`, `GEMINI_TIMEOUT`,
`INVALID_GEMINI_OUTPUT`, `MEDIA_PROCESSING_FAILED`, `MCP_UNAVAILABLE`,
`QUERY_REJECTED`, `UNAUTHORIZED`, `NOT_FOUND`, `INVALID_TRANSITION`.

## Async analysis job model

``` text
POST .../analyze  → 202 {analysis_run_id, status:"queued"}
                     writes a row to analysis_runs
GET  .../analysis/{id} → {status, step, findings_count, error_code}
                     polled by the frontend stepper (§30 AsyncBoundary)
```

State persists in `analysis_runs` (§14), never in process memory ---
required because Cloud Run scales to zero and runs multiple instances.

------------------------------------------------------------------------

# 40. Backend and Frontend Structure

``` text
services/api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── policies.py
│   │   ├── clips.py
│   │   ├── scenes.py
│   │   ├── findings.py
│   │   ├── analysis.py
│   │   └── agent.py
│   ├── agents/
│   │   └── scenerights_supervisor.py    # ADK agent
│   ├── tools/
│   │   ├── clickhouse_mcp.py            # tool_filter config
│   │   ├── policy_tool.py
│   │   ├── video_tool.py                # FFmpeg keyframe extraction
│   │   └── report_tool.py               # deterministic template, no Gemini
│   ├── services/
│   │   ├── storage.py
│   │   ├── policy.py
│   │   ├── continuity.py
│   │   └── findings.py
│   ├── models/
│   └── schemas/
└── tests/

services/mcp-clickhouse/
└── deploy/                              # Cloud Run config for the partner
                                          # MCP server, Streamable HTTP

apps/web/
├── app/
│   ├── page.tsx
│   ├── policies/
│   ├── scenes/
│   └── findings/
├── components/
│   ├── layout/
│   ├── video/
│   ├── findings/
│   ├── continuity/
│   ├── policy/
│   └── agent/            # AgentPanel, McpActivityRail
├── lib/
│   ├── api.ts
│   ├── types.ts
│   └── constants.ts
└── public/
```

------------------------------------------------------------------------

# 41. Environment Template

`.env.example`

``` bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
GEMINI_MODEL=
GCS_BUCKET=

# ClickHouse (application write path)
CLICKHOUSE_HOST=
CLICKHOUSE_PORT=
CLICKHOUSE_USER=
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=

# mcp-clickhouse client path (FastAPI/ADK -> MCP service)
MCP_CLICKHOUSE_URL=                    # Streamable HTTP endpoint, own Cloud Run service
MCP_CLICKHOUSE_AUTH_TOKEN=

# mcp-clickhouse Cloud Run service ONLY (MCP -> ClickHouse Cloud)
# These MUST be the read-only scenerights_mcp_ro credentials and MUST NOT
# reuse CLICKHOUSE_USER / CLICKHOUSE_PASSWORD from the application write path.
MCP_CH_HOST=
MCP_CH_PORT=
MCP_CH_USER=scenerights_mcp_ro
MCP_CH_PASSWORD=
MCP_CH_DATABASE=
CLICKHOUSE_ALLOW_WRITE_ACCESS=false
CLICKHOUSE_ALLOW_DROP=false
CHDB_ENABLED=false

# Demo access (no login/signup — single shared token)
DEMO_ACCESS_TOKEN=
DEMO_PROJECT_ID=

# App
API_BASE_URL=
APP_ENV=development
```

Never place real secrets in `.env.example`. Bound via Secret Manager in
deployed environments (`--set-secrets`).

------------------------------------------------------------------------

# 42. Test Strategy

## Unit Tests

``` text
UT-001 Policy rule schema validation
UT-002 Finding schema validation
UT-003 Severity derivation from policy_rules.priority
UT-004 review_status transition validation
UT-005 Token/authorization helper (demo-access token, §33)
UT-006 File-type/size validation
UT-007 source_quote substring validator
UT-008 ClickHouse result normalization
UT-009 Agent tool-routing decision helper
```

## Integration Tests

``` text
IT-POL-01 Upload → Cloud Storage + policy_documents row → Extraction
IT-POL-02 Extraction → policy_rules row linked by policy_id → source_quote validation → Rule Approval
IT-SCN-01 Create scene → scenes row → set reference → reference_clip_id persists
IT-VID-01 Upload → Media Metadata → FFmpeg keyframes
IT-CON-01 Scene → Reference → Analysis → findings written
IT-FND-01 Observation → Policy Match → Finding
IT-REV-01 Finding → Decision insert → findings_current updates
IT-CH-01  Finding → ClickHouse append-only persistence
IT-AG-01  Agent → MCP → ClickHouse (scoped view) → Answer
IT-JOB-01 analyze → 202 + analysis_run_id → poll → completed
IT-IDEM-01 Duplicate POST /analyze with same Idempotency-Key does not
           duplicate findings
```

## System Tests

``` text
ST-CON-01 Missing necklace, clear visibility
ST-CON-02 Necklace occluded → not_visible
ST-CON-03 Blue mug → red mug
ST-STATE-01 Resolve finding → next MCP-backed query reflects it, <2s
ST-POL-03 Rejected rule excluded from matching
ST-FND-01 Finding source attribution matches the approved rule
ST-REP-01 Deterministic report contains decisions, no Gemini call made
```

## AI Quality Tests

``` text
AI-STR-01 Malformed structured output → bounded retry → partial/failed
AI-CON-01 Reference/comparison reasoning on paired keyframes
AI-CON-02 Occlusion awareness (not_visible, never absent)
AI-CON-03 No invented object state
AI-CON-04 Take A vs Take A → zero findings (false-positive control —
          highest-value single test in the suite)
AI-CON-05 Repeated controlled input → stable semantic classification; explanation wording may vary
AI-POL-01 Policy rule extraction accuracy
AI-POL-02 source_quote passes substring validation
AI-POL-03 No invented company rule
AI-POL-04 Prompt injection resistance (document)
AI-INJ-01 Prompt injection resistance (text visible in video frame)
```

## MCP Tests

``` text
MCP-01 Official MCP connectivity (Streamable HTTP)
MCP-02 findings_current query returns correct unresolved rows
MCP-04 State change (resolve) reflected in the next query
MCP-05 Schema access restricted to scoped views, not base tables
MCP-06 MCP unavailable → agent states so, no hallucinated state
MCP-07 Destructive prompt ("drop the findings table") rejected
MCP-08 chDB tools absent from the agent's tool list
MCP-09 Destructive SQL rejected by ClickHouse itself (grant-level),
       not merely declined by the model
MCP-10 Agent query scoped to the seeded project cannot surface rows
       outside it (verifies the pre-filtered-view boundary, §5)
```

## Security Tests

``` text
SEC-T04 Missing/invalid demo-access token → 401
SEC-T05 Secret exposure scan (no credentials in frontend bundle)
SEC-T06 Signed storage URL TTL and scope
SEC-T07 Prompt injection in policy document (paired with AI-POL-04)
SEC-T08 Arbitrary SQL attempt via agent query rejected
SEC-T09 Invalid review_status transition rejected
SEC-T10 gitleaks scan passes on every commit
SEC-T11 CI dependency allowlist/import/config compliance gate (§29) passes
API-CON-01 Endpoint DTOs, Pydantic schemas, TypeScript types, ClickHouse columns, and enums use the authoritative identifiers/status vocabulary
```

## UAT

``` text
UAT-POL-01 Demo user uploads and approves policy
UAT-CON-01 Demo user sets reference take
UAT-CON-02 Reviewer understands the necklace finding without explanation
UAT-CON-03 Reviewer understands the mug finding without explanation
UAT-REV-01 Reviewer confirms and resolves a finding
UAT-MCP-01 User asks unresolved-state question, receives a live answer
           with visible tool trace
UAT-MCP-02 User repeats the query after resolving a finding, sees the
           updated answer via split-screen before/after
UAT-DEMO-01 Full demo completes within 3 minutes, rehearsed 5×
           consecutively on the deployed URL
DEMO-02 Full demo run under throttled network conditions
DEMO-03 Reset-to-clean-state (POST /seed) works reliably between runs
PERF-01 Analysis completes within NFR-020 on the real demo clips
```

------------------------------------------------------------------------

# 43. V-Model Traceability Matrix (P0 scope, 100% coverage target)

  ----------------------------------------------------------------------------------------------------------------
  Requirement       Use Case       Design Component   Implementation Artifact                       Test
  ----------------- -------------- ------------------ --------------------------------------------- --------------
  FR-004            UC-001         Policy Upload      `services/api/app/api/policies.py`            IT-POL-01
                                   API + GCS                                                        

  FR-007            UC-002         Gemini Policy      `agents/.../policy_tool.py`,                  AI-POL-01
                                   Extractor          `prompts/policy_extraction.md`                

  FR-009            UC-002         source_quote       `services/policy.py::validate_source_quote`   AI-POL-02,
                                   validator                                                        UT-007

  FR-008            UC-003         Rule Review UI/API `apps/web/.../policy/`, `api/policies.py`     UAT-POL-01

  FR-004            UC-001         Policy document    `database/clickhouse/policy_documents.sql`,  IT-POL-01
                                   persistence         `api/policies.py`

  FR-019/021        UC-005         Scene/reference     `database/clickhouse/scenes.sql`,            IT-SCN-01
                                   persistence         `api/scenes.py`

  FR-015            UC-004         Clip Upload API    `api/clips.py`                                IT-VID-01

  FR-021            UC-005         Scene Reference    `api/scenes.py`                               UAT-CON-01
                                   API/UI                                                           

  FR-024            UC-006         Gemini Continuity  `tools/video_tool.py`,                        AI-CON-01
                                   Comparator (paired `prompts/continuity_compare.md`               
                                   frames)                                                          

  FR-025            UC-006, UC-009 Assessment enum    `services/continuity.py`                      AI-CON-02,
                                   logic                                                            ST-CON-02

  FR-026            UC-008         Colour comparison  `services/continuity.py`                      ST-CON-03

  FR-027            UC-007         Presence           `services/continuity.py`                      ST-CON-01
                                   comparison                                                       

  FR-031            UC-010         Policy matcher     `services/findings.py`                        ST-FND-01

  FR-034/037        UC-011         Decision API →     `api/findings.py`                             IT-REV-01,
                                   `decisions` insert                                               UAT-REV-01

  FR-039            UC-012         Agent tool router  `agents/scenerights_supervisor.py`            MCP-02

  FR-040            UC-012         MCP failure        `tools/clickhouse_mcp.py`                     MCP-06
                    (failure)      handling                                                         

  FR-044            ---            Append-only        `database/clickhouse/findings.sql`            IT-CH-01
                                   findings table                                                   

  FR-047            UC-012         Official           `services/mcp-clickhouse/`                    MCP-01
                                   mcp-clickhouse,                                                  
                                   own Cloud Run                                                    
                                   service                                                          

  FR-048            UC-012         MCP Activity rail  `apps/web/.../agent/McpActivityRail.tsx`      UAT-MCP-01,
                                                                                                    UAT-MCP-02

  FR-053            UC-006         Async job model    `api/analysis.py`, `analysis_runs` table      IT-JOB-01

  SEC-004           all            Demo-token         `api/deps.py`                                 SEC-T04
                                   authorization                                                    

  SEC-007/008/009   UC-012         MCP grant +        `services/mcp-clickhouse/config`              MCP-08,
                                   tool_filter                                                      MCP-09,
                                                                                                    SEC-T08

  AIR-002           UC-002, UC-006 Pydantic schema    `schemas/`                                    AI-STR-01
                                   validator                                                        

  AIR-005           UC-002         source_quote       `services/policy.py`                          AI-POL-03
                                   guardrail                                                        

  ---               ---            findings_current   `database/clickhouse/findings_current.sql`    ST-STATE-01,
                                   state derivation                                                 MCP-04

  ---               ---            False-positive     `tests/ai_quality/`                           AI-CON-04
                                   control                                                          
  ----------------------------------------------------------------------------------------------------------------

NFRs, P1/P2 requirements, and the full 30-UC v6 catalogue are
intentionally unverified in this matrix for the hackathon build --- see
§28 and §31.

------------------------------------------------------------------------

# 44. Acceptance Criteria --- Critical Happy Path

## AC-001 Policy Upload and Approval

``` text
Given a valid demo-access token
And a fictional policy document
When the document is uploaded
Then it is stored privately
And Gemini extracts three structured candidate rules, each with a
    source_quote that passes substring validation
And the UI shows source attribution
And the rules are not active until approved.
```

## AC-002 Continuity Comparison

``` text
Given Take A is the reference
And Take A clearly shows a silver necklace and blue mug
And Take B clearly omits the necklace and shows a red mug
When continuity analysis completes on paired keyframes
Then the system creates a necklace presence finding (ai_assessment=absent)
And a mug colour-change finding (ai_assessment=changed)
And neither finding has a review_status other than 'open'.
```

## AC-003 Occlusion Safety

``` text
Given the reference necklace is visible
And the comparison neck region is substantially occluded (Take C)
When analysis completes
Then the necklace ai_assessment is not_visible
And the system does not label it definitively absent
And no actionable finding requiring resolution is raised for it.
```

## AC-004 Policy Grounding

``` text
Given an approved rule says the hero mug remains blue
And Gemini observes a red mug in Take B
When a finding is generated
Then the finding cites the approved policy_rule_id, rule text, and
    source_quote.
```

## AC-005 MCP Runtime

``` text
Given unresolved findings exist in findings_current
When the user asks the SceneRights agent what remains unresolved
Then the Gemini agent invokes the official ClickHouse MCP integration
    (Streamable HTTP, read-only scoped view)
And answers using only the returned rows.
```

## AC-006 Updated State

``` text
Given a reviewer inserts a 'resolved' decision for the necklace finding
When the user asks again what remains unresolved
Then the next MCP-backed answer, queried against findings_current,
    excludes the resolved necklace finding, within 2 seconds.
```

## AC-007 False-Positive Control (new)

``` text
Given Take A is compared against itself
When continuity analysis completes
Then zero findings are created.
```

------------------------------------------------------------------------

# 45. Error Handling Requirements

  -------------------------------------------------------------------------
  Error                   Code                      Required UX
  ----------------------- ------------------------- -----------------------
  Policy upload failure   UPLOAD_FAILED             Show error + retry

  Policy parse failure    PARSE_FAILED              Mark document failed;
                                                    no rules fabricated

  Gemini timeout          GEMINI_TIMEOUT            Retryable analysis
                                                    failure shown

  Invalid Gemini JSON     INVALID_GEMINI_OUTPUT     Bounded retry, then
                                                    fail/partial

  Video upload failure    UPLOAD_FAILED             Preserve project; retry
                                                    upload

  FFmpeg failure          MEDIA_PROCESSING_FAILED   Mark clip processing
                                                    failed

  ClickHouse unavailable  MCP_UNAVAILABLE           Current-state query
                                                    fails transparently,
                                                    distinct UI state

  MCP query rejected      QUERY_REJECTED            Agent states it cannot
                                                    run that query

  Unauthorized access     UNAUTHORIZED              401 without resource
                                                    leakage

  No findings             ---                       Explicit clean/empty
                                                    state, never blank

  No matching policy      ---                       "No applicable approved
                                                    policy found"

  Invalid state           INVALID_TRANSITION        Rejected server-side,
  transition                                        current state unchanged
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 46. Definition of Ready for Coding

``` text
[ ] Google/Partner AI restriction accepted (§1).
[ ] ClickHouse track confirmed.
[ ] google-adk / google-genai confirmed as the SDK choice.
[ ] Fictional demo policy finalized (§7 — exactly 3 rules).
[ ] Three original demo clips planned and scheduled (§26).
[ ] P0 scope accepted (§28) — no scope additions without removing
    something else from P0.
[ ] Environment variable list accepted (§41).
[ ] ClickHouse Cloud project available.
[ ] Google Cloud project available; $100 credit form submitted.
[ ] Explicit agreement: no login/signup will be built (§33).
```

------------------------------------------------------------------------

# 47. Coding-Agent Master Instruction

When an AI coding assistant receives this file, it treats this document
as the authoritative product contract, subordinate only to the CI
compliance gate (§29) and the AI Coding Agent Instructions (§29). See
§29 for the full rule list. If any requirement here appears technically
blocked, report the blocker before changing scope --- do not silently
drop a P0 item or silently add scope beyond §28's P0 list.

------------------------------------------------------------------------

## End of SceneRights AI v6.2.2 Master Specification
