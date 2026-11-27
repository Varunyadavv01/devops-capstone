CREATE TABLE tasks (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120 AND btrim(title) <> ''),
    description TEXT NOT NULL DEFAULT '' CHECK (char_length(description) <= 2000),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT statement_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT statement_timestamp(),
    CHECK (updated_at >= created_at)
);

CREATE TABLE seed_runs (
    name TEXT PRIMARY KEY
);
