# SceneRights AI — Milestone 2
# Policy Ingestion & Gemini Rule Extraction Specification

**Project:** SceneRights AI
**Milestone:** 2
**Master Specification:** SceneRights AI v6.2.2
**Scope:** P0
**Status:** Implementation Specification

---

# 1. Authority

This document defines Milestone 2 implementation requirements only.

The authoritative source of truth remains:

`SceneRights_AI_v6_2_2_Master_Spec.md`

If this document conflicts with the Master Spec, the Master Spec wins.

Milestones 1A–1D are assumed complete and must not be redesigned.

---

# 2. Goal

Implement the complete P0 company-policy workflow:

1. Upload a policy document.
2. Store the original document privately in Google Cloud Storage.
3. Extract deterministic text from the document.
4. Persist policy document metadata.
5. Send parsed policy text to Gemini through Vertex AI.
6. Receive structured candidate policy rules.
7. Validate every `source_quote` against the parsed source text.
8. Automatically reject invalid candidate rules.
9. Present valid extracted rules for human review.
10. Allow the demo user to Approve or Reject each rule.
11. Persist rule status in ClickHouse.
12. Make approved rules available to later continuity analysis.

This milestone implements UC-001, UC-002 and UC-003.

---

# 3. P0 Workflow

The required workflow is:

```text
Policy File
    |
    v
FastAPI Upload Validation
    |
    v
Private Google Cloud Storage
    |
    v
Deterministic Text Extraction
    |
    +----------------------+
    |                      |
    v                      v
ClickHouse            Gemini / Vertex AI
policy_documents           |
                            v
                     Candidate Rules
                            |
                            v
                  Exact source_quote Check
                     /              \
                  PASS              FAIL
                   |                  |
                   v                  v
             Review Queue       Auto-Reject
                   |
             +-----+------+
             |            |
          Approve       Reject
             |            |
             +-----+------+
                   |
                   v
            ClickHouse policy_rules