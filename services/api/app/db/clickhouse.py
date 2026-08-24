import os
from pathlib import Path
import clickhouse_connect
from app.config import settings


def get_clickhouse_client():
    """Returns an authenticated clickhouse-connect client using app write credentials."""
    return clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DATABASE,
        secure=settings.CLICKHOUSE_SECURE,
    )


def apply_migrations():
    """Applies all authoritative DDL SQL scripts in database/clickhouse."""
    client = get_clickhouse_client()
    
    # Path to database/clickhouse DDL scripts
    ddl_dir = Path(__file__).resolve().parents[4] / "database" / "clickhouse"
    if not ddl_dir.exists():
        # Fallback if relative path differs
        ddl_dir = Path("database/clickhouse")

    sql_files = sorted(list(ddl_dir.glob("*.sql")))
    applied = []
    
    for sql_file in sql_files:
        if sql_file.name == "00_init.sql" or sql_file.name == "11_mcp_user_and_views.sql":
            # Skip master runner and MCP user DDL for app migrations
            continue
        sql = sql_file.read_text(encoding="utf-8").strip()
        if sql:
            client.command(sql)
            applied.append(sql_file.name)
            
    return applied

