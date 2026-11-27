WITH first_run AS (
    INSERT INTO seed_runs (name)
    VALUES ('demo-v1')
    ON CONFLICT DO NOTHING
    RETURNING name
)
INSERT INTO tasks (title, description, status, priority)
SELECT demo.title, demo.description, demo.status, demo.priority
FROM first_run
CROSS JOIN (VALUES
    ('Review deployment checklist', 'Confirm image tags and rollback steps.', 'in_progress', 'high'),
    ('Document environment variables', 'Record local configuration and safe defaults.', 'pending', 'medium'),
    ('Test database restore', 'Restore a synthetic backup into an isolated database.', 'pending', 'high'),
    ('Verify application health checks', 'Check process liveness and database readiness.', 'completed', 'medium'),
    ('Clean up local build artifacts', 'Remove temporary files from the demo workspace.', 'completed', 'low')
) AS demo(title, description, status, priority);
