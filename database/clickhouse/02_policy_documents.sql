CREATE TABLE IF NOT EXISTS policy_documents
(
    project_id String,
    policy_id String,
    filename String,
    gcs_uri String,
    status LowCardinality(String),
    created_at DateTime,
    updated_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, policy_id);

