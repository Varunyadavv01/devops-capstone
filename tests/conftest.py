import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from app import create_app


@pytest.fixture
def db_settings():
    dsn = os.environ.get("TASKOPS_TEST_DSN")
    if not dsn:
        pytest.fail("Set TASKOPS_TEST_DSN for a dedicated taskops_test database or run bash scripts/test.sh.")
    settings = conninfo_to_dict(dsn)
    if settings.get("dbname") != "taskops_test":
        pytest.fail("Integration tests require a database named taskops_test.")
    schema = f"case_{uuid4().hex}"
    with psycopg.connect(**settings, connect_timeout=2, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            yield {**settings, "options": f"-csearch_path={schema}"}
        finally:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def app(db_settings):
    return create_app({"TESTING": True, "DB_SETTINGS": db_settings, "SEED_DEMO": False})


@pytest.fixture
def client(app):
    return app.test_client()
