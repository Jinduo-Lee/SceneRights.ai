# ClickHouse MCP Specification (v6.2.2 Baseline)

## MCP Service Config
- Service name: `scenerights-mcp-clickhouse` (Cloud Run)
- Transport: Streamable HTTP
- Database user: `scenerights_mcp_ro`
- Permissions: `SELECT`-only on project-scoped views (`readonly=1`)
- Configuration flags:
  - `CHDB_ENABLED=false`
  - `CLICKHOUSE_ALLOW_WRITE_ACCESS=false`
  - `CLICKHOUSE_ALLOW_DROP=false`
- Tool filter: Restricted via ADK `tool_filter` to `run_select_query` and `list_tables`.

