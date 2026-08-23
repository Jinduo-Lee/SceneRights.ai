# SceneRights AI

> **Agentic Production Compliance, Continuity, Policy Intelligence & Visual Review**
>
> *This repository was created for the Agentic Cinema Hackathon and contains no code predating the contest period.*

**Competition:** Agentic Cinema: The Blockbuster Hackathon  
**Track:** ClickHouse  
**Specification Baseline:** v6.2.2  

---

## 1. Overview

SceneRights AI is a Gemini-powered production supervisor for filmmakers and studio crews. Built for the Agentic Cinema Hackathon (ClickHouse Track), it provides:

- **Company Policy Intelligence:** Studio policy upload and structured candidate rule extraction with verbatim source quote grounding.
- **Cross-Shot Continuity:** Gemini-powered paired-keyframe comparison for visual continuity (e.g. necklace presence, mug colour).
- **Policy-Grounded Visual Review:** Detection matched against approved studio policies before presentation to human reviewers.
- **Auditable Production State:** ClickHouse event sourcing using append-only `findings` and `decisions` tables, with current state derived via the `findings_current` VIEW.
- **ClickHouse MCP Agent Integration:** Interactive "Ask SceneRights" agent powered by Google ADK / Gemini and official `mcp-clickhouse` over Streamable HTTP with a read-only database user (`scenerights_mcp_ro`).

---

## 2. Architecture & Data Flow

```text
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

---

## 3. Repository Structure

```text
scenerights-ai/
├── apps/
│   └── web/                   # Next.js TypeScript frontend
├── services/
│   ├── api/                   # FastAPI Python 3.12 backend
│   └── mcp-clickhouse/        # Deployment configuration for official mcp-clickhouse
├── agents/
│   └── supervisor/            # Google ADK agent definition
├── tools/
│   ├── video/                 # Deterministic FFmpeg keyframe tools
│   └── clickhouse/            # ClickHouse MCP query helpers
├── prompts/                   # Gemini prompt templates
├── database/
│   └── clickhouse/            # Authoritative ClickHouse DDL & migrations
├── samples/
│   ├── fictional-policy/      # Fictional Northstar policy sample
│   └── original-demo-footage/ # Original demo video clips
├── docs/                      # Technical documentation
├── .env.example
├── LICENSE                    # Apache-2.0
└── README.md
```

---

## 4. License

Licensed under the [Apache License, Version 2.0](LICENSE).

