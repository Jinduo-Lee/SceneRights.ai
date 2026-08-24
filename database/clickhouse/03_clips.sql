CREATE TABLE IF NOT EXISTS clips
(
    project_id String,
    clip_id String,
    scene_id String,
    role LowCardinality(String),
    gcs_uri String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id, clip_id);

