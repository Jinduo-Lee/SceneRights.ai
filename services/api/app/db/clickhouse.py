import os
from pathlib import Path
import clickhouse_connect
from app.config import settings


def clean_host_and_port(raw_host: str, raw_port: int) -> tuple[str, int]:
    """Strips scheme prefixes (http://, https://) and trailing ports/slashes from raw host string."""
    host = raw_host.strip()
    port = raw_port
    if "://" in host:
        host = host.split("://", 1)[1]
    if ":" in host:
        parts = host.split(":", 1)
        host = parts[0]
        if parts[1].split("/")[0].isdigit():
            port = int(parts[1].split("/")[0])
    host = host.rstrip("/")
    return host, port


def get_clickhouse_client():
    """Returns an authenticated clickhouse-connect client using app write credentials."""
    clean_host, clean_port = clean_host_and_port(
        settings.CLICKHOUSE_HOST, settings.CLICKHOUSE_PORT
    )
    return clickhouse_connect.get_client(
        host=clean_host,
        port=clean_port,
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
        if sql_file.name in ("00_init.sql", "11_mcp_user_and_views.sql"):
            # Skip master runner and MCP user DDL for app migrations
            continue
        sql = sql_file.read_text(encoding="utf-8").strip()
        if sql:
            client.command(sql)
            applied.append(sql_file.name)
            
    return applied
