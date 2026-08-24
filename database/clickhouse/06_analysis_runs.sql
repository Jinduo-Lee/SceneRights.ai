CREATE TABLE IF NOT EXISTS analysis_runs
(
    project_id String,
    scene_id String,
    analysis_run_id String,
    status LowCardinality(String),
    step LowCardinality(String),
    error_code Nullable(String),
    started_at DateTime,
    completed_at Nullable(DateTime)
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, started_at);

