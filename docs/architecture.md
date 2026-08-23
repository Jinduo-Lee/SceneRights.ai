# Architecture Specification (v6.2.2 Baseline)

## Two-Lane Model
1. **Write Lane:** FastAPI backend writes to ClickHouse Cloud via `clickhouse-connect` (append-only `findings` and `decisions`).
2. **Read Lane:** Gemini ADK Agent reads state via official `mcp-clickhouse` server over Streamable HTTP using read-only `scenerights_mcp_ro` user (`readonly=1`, `CHDB_ENABLED=false`).

## Derived Current State
- Current finding state is derived dynamically via `findings_current` VIEW using `argMax(review_status, created_at)` over the `decisions` table.
- Mutations (`ALTER ... UPDATE`) are strictly prohibited. All human decisions are `INSERT` statements into `decisions`.

## Media Processing Strategy
- FFmpeg extracts 3–5 keyframes per clip at fixed timestamps.
- Paired keyframes are evaluated by Gemini in structured-output format.
- Occluded objects are assigned `ai_assessment = 'not_visible'`, never `absent`.

