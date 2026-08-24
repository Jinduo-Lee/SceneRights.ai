CREATE TABLE IF NOT EXISTS policy_rules
(
    project_id String,
    policy_id String,
    policy_rule_id String,
    document_name String,
    policy_type LowCardinality(String),
    rule_text String,
    source_quote String,
    priority LowCardinality(String),
    status LowCardinality(String),
    version UInt16,
    effective_date Nullable(DateTime),
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, policy_rule_id);

