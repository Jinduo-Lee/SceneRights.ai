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

