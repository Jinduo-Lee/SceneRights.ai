CREATE TABLE IF NOT EXISTS scenes
(
    project_id String,
    scene_id String,
    name String,
    reference_clip_id String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (project_id, scene_id);

