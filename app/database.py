import os
from pathlib import Path
from threading import Lock

import psycopg
from psycopg.rows import dict_row

SQL_DIR = Path(__file__).resolve().parent.parent / "migrations"


class Database:
    def __init__(self, config):
        self.settings = config.get("DB_SETTINGS") or {
            "host": os.environ.get("DB_HOST", "127.0.0.1"),
            "port": os.environ.get("DB_PORT", "5432"),
            "dbname": os.environ.get("POSTGRES_DB", "taskops"),
            "user": os.environ.get("DB_USER", "taskops"),
            "password": os.environ.get("DB_PASSWORD", ""),
            "sslmode": os.environ.get("DB_SSLMODE", "prefer"),
            "options": "-csearch_path=taskops",
        }
        self.seed = config.get("SEED_DEMO", os.environ.get("SEED_DEMO", "0") == "1")
        self.initialized = False
        self.lock = Lock()

    def connect(self):
        settings = self.settings.copy()
        settings["options"] = (
            settings.get("options", "")
            + " -cstatement_timeout=2000 -clock_timeout=1500 -ctimezone=UTC"
        ).strip()
        return psycopg.connect(
            **settings, connect_timeout=2, application_name="taskops", row_factory=dict_row
        )

    def initialize(self):
        if self.initialized:
            return
        with self.lock:
            if self.initialized:
                return
            with self.connect() as connection:
                connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended('taskops:' || current_schema(), 0))"
                )
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)"
                )
                applied = {
                    row["version"] for row in connection.execute("SELECT version FROM schema_migrations")
                }
                for migration in sorted(SQL_DIR.glob("[0-9][0-9][0-9]_*.sql")):
                    if migration.name not in applied:
                        connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
                        connection.execute("INSERT INTO schema_migrations VALUES (%s)", (migration.name,))
                if self.seed:
                    connection.execute((SQL_DIR / "seed_demo.sql").read_text(encoding="utf-8"))
            self.initialized = True

    def query(self, statement, params=(), *, one=False):
        self.initialize()
        with self.connect() as connection:
            cursor = connection.execute(statement, params)
            return cursor.fetchone() if one else cursor.fetchall()

    def ready(self):
        try:
            self.query("SELECT id FROM tasks LIMIT 0")
        except psycopg.Error:
            return False
        return True
