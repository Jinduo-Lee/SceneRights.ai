CREATE TABLE IF NOT EXISTS decisions
(
    project_id String,
    finding_id String,
    review_status LowCardinality(String),
    previous_status LowCardinality(String),
    reviewer String,
    comment String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, finding_id, created_at);

