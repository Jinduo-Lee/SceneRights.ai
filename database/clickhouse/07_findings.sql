CREATE TABLE IF NOT EXISTS findings
(
    project_id String,
    scene_id String,
    finding_id String,
    analysis_run_id String,
    finding_type LowCardinality(String),
    object_type String,
    object_label String,
    reference_clip String,
    comparison_clip String,
    ai_assessment LowCardinality(String),
    model_assessment LowCardinality(String),
    severity LowCardinality(String),
    policy_rule_id String,
    policy_rule_version UInt16,
    policy_document String,
    policy_rule String,
    source_quote String,
    timestamp_ms UInt32,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, created_at);

