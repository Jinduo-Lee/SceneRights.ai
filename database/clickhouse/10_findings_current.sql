CREATE OR REPLACE VIEW findings_current AS
SELECT
    f.project_id,
    f.scene_id,
    f.finding_id,
    f.finding_type,
    f.severity,
    f.object_type,
    f.object_label,
    f.ai_assessment,
    f.policy_rule_id,
    f.policy_rule,
    f.source_quote,
    if(empty(d.review_status), 'open', d.review_status) AS review_status,
    d.reviewer AS last_reviewer,
    d.max_created_at AS decided_at
FROM findings AS f
LEFT JOIN
(
    SELECT
        project_id,
        finding_id,
        argMax(review_status, created_at) AS review_status,
        argMax(reviewer, created_at) AS reviewer,
        max(created_at) AS max_created_at
    FROM decisions
    GROUP BY project_id, finding_id
) AS d
    ON f.project_id = d.project_id
   AND f.finding_id = d.finding_id;
