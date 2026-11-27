from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import psycopg
import pytest

from app import create_app
from app.database import Database


def test_crud_and_persistence(client, db_settings):
    create = client.post("/api/tasks", json={
        "title": "Verify <deployment>",
        "description": "O'Reilly test; SELECT 1;",
        "priority": "high",
    })
    assert create.status_code == 201
    task, url = create.json, create.headers["Location"]
    assert url == f"/api/tasks/{task['id']}"
    assert task["status"] == "pending"
    assert task["description"] == "O'Reilly test; SELECT 1;"
    assert task["created_at"] == task["updated_at"]
    assert client.get(url).json == task
    assert client.get("/api/tasks").json == {"tasks": [task]}

    restarted_client = create_app({
        "TESTING": True, "DB_SETTINGS": db_settings, "SEED_DEMO": False,
    }).test_client()
    assert restarted_client.get(url).json == task
    update = restarted_client.put(url, json={
        "title": "Deployment complete", "status": "completed", "priority": "low",
    })
    assert update.status_code == 200
    updated = update.json
    assert updated["id"] == task["id"] and updated["created_at"] == task["created_at"]
    assert datetime.fromisoformat(updated["updated_at"]) >= datetime.fromisoformat(task["updated_at"])
    assert updated["status"] == "completed" and updated["priority"] == "low"
    assert updated["description"] == ""

    deleted = client.delete(url)
    assert deleted.status_code == 204 and not deleted.data
    assert restarted_client.get(url).status_code == 404
    assert client.delete(url).status_code == 404


def test_status_filtering_and_stats(client):
    for status in ["pending", "in_progress", "completed", "completed"]:
        response = client.post("/api/tasks", json={"title": f"Task {status}", "status": status})
        assert response.status_code == 201
    assert client.get("/api/stats").json == {
        "total": 4, "pending": 1, "in_progress": 1, "completed": 2,
    }
    for status, count in [("pending", 1), ("in_progress", 1), ("completed", 2)]:
        tasks = client.get(f"/api/tasks?status={status}").json["tasks"]
        assert len(tasks) == count and {task["status"] for task in tasks} == {status}
    assert client.get("/api/tasks?status=wrong").status_code == 400
    assert client.get("/api/tasks?status=pending&status=completed").status_code == 400


@pytest.mark.parametrize(("data", "content_type", "status"), [
    ("{{", "application/json", 400),
    ("[]", "application/json", 400),
    ('{"title":"X","status":"done"}', "application/json", 400),
    ('{"title":"X","priority":"urgent"}', "application/json", 400),
    ('{"title":"X"}', "text/plain", 415),
    ('{"title":"' + "a" * 32768 + '"}', "application/json", 413),
])
def test_invalid_requests(client, data, content_type, status):
    reply = client.post("/api/tasks", data=data, content_type=content_type)
    assert reply.status_code == status
    assert reply.json["request_id"] == reply.headers["X-Request-ID"]
    assert reply.json["error"]["message"]


@pytest.mark.parametrize("task_id", [0, 999_999, 2_147_483_648])
def test_missing_tasks(client, task_id):
    url = f"/api/tasks/{task_id}"
    assert client.get(url).status_code == 404
    assert client.put(url, json={"title": "Replacement"}).status_code == 404
    assert client.delete(url).status_code == 404


def test_health_release_and_metrics(client, app):
    app.config["RELEASE"] = {
        "name": "TaskOps", "version": "1.2.3", "git_commit": "0123456789",
        "build_date": "2026-03-01",
    }
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json == {"status": "ok", **app.config["RELEASE"]}
    assert client.get("/api/version").json == app.config["RELEASE"]
    assert client.get("/health/live").json == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200 and ready.json == {"status": "ready", "database": "available"}
    assert b"v1.2.3" in client.get("/").data

    assert client.post("/api/tasks", json={"title": "sensitive task text"}).status_code == 201
    assert client.get("/api/tasks/987654321").status_code == 404
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.content_type.startswith("text/plain")
    assert "taskops_tasks_created_total 1.0" in metrics.text
    assert "taskops_database_available 1.0" in metrics.text
    for name in ("taskops_http_requests_total", "taskops_http_responses_total",
                 "taskops_http_request_duration_seconds_bucket", "taskops_application_errors_total"):
        assert name in metrics.text
    assert 'endpoint="/api/tasks/<int:task_id>"' in metrics.text
    assert "987654321" not in metrics.text and "sensitive task text" not in metrics.text


def test_schema_constraints_and_transaction_rollback(app):
    db = app.extensions["database"]
    assert db.ready()
    assert db.query("SELECT version FROM schema_migrations", one=True)["version"] == "001_initial.sql"
    with pytest.raises(psycopg.errors.CheckViolation), db.connect() as connection:
        connection.execute("INSERT INTO tasks (title) VALUES (%s)", ("Roll back this task",))
        connection.execute("INSERT INTO tasks (title, priority) VALUES (%s, %s)", ("Invalid", "urgent"))
    assert db.query("SELECT title FROM tasks") == []

    with pytest.raises(psycopg.errors.CheckViolation), db.connect() as connection:
        connection.execute("INSERT INTO tasks (title, status) VALUES (%s, %s)", ("Invalid", "done"))


def test_concurrent_schema_setup_and_idempotent_seed(db_settings):
    config = {"DB_SETTINGS": db_settings, "SEED_DEMO": True}
    instances = [Database(config) for _ in range(4)]
    with ThreadPoolExecutor(max_workers=len(instances)) as executor:
        assert list(executor.map(Database.ready, instances)) == [True] * len(instances)
    db = instances[0]
    assert db.query("SELECT count(*) FROM schema_migrations", one=True)["count"] == 1
    assert db.query("SELECT count(*) FROM tasks", one=True)["count"] == 5
    db.query("DELETE FROM tasks WHERE id = (SELECT min(id) FROM tasks) RETURNING id")
    assert Database(config).query("SELECT count(*) FROM tasks", one=True)["count"] == 4


def test_readiness_recovers_after_connection_failure(client, app):
    db = app.extensions["database"]
    original_port = db.settings.get("port", "5432")
    db.settings = {**db.settings, "port": "1"}
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/live").status_code == 200
    db.settings["port"] = original_port
    assert client.get("/health/ready").status_code == 200
