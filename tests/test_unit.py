import psycopg
import pytest

from app import create_app, release_metadata
from app.routes import PRIORITIES, STATUSES, ValidationError, validate_task


def test_defaults_and_trimming():
    assert validate_task({"title": "  Review checks  ", "description": "  A note\n"}) == (
        "Review checks", "A note", "pending", "medium"
    )
    assert validate_task({"title": "x" * 120, "description": "y" * 2000})[:2] == ("x" * 120, "y" * 2000)


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("priority", PRIORITIES)
def test_valid_status_and_priority(status, priority):
    assert validate_task({"title": "Task", "status": status, "priority": priority})[2:] == (status, priority)


@pytest.mark.parametrize("payload", [
    None, [], "string", {}, {"title": " "}, {"title": True}, {"title": "a" * 121},
    {"title": "one\0two"}, {"title": "\ud800"}, {"title": "Task", "description": None},
    {"title": "Task", "description": "a" * 2001}, {"title": "Task", "status": "done"},
    {"title": "Task", "status": {}}, {"title": "Task", "priority": "urgent"},
    {"title": "Task", "priority": []}, {"title": "Task", "updated_at": "tomorrow"},
])
def test_invalid_task(payload):
    with pytest.raises(ValidationError):
        validate_task(payload)


def test_release_metadata():
    assert release_metadata({}) == {
        "name": "TaskOps", "version": "0.1.0", "git_commit": None, "build_date": None,
    }
    assert release_metadata({
        "APP_VERSION": "2.4.0-canary.1", "GIT_COMMIT_SHA": "f7f7fff",
        "BUILD_DATE": "2026-01-12T11:03:00Z",
    }) == {
        "name": "TaskOps", "version": "2.4.0-canary.1", "git_commit": "f7f7fff",
        "build_date": "2026-01-12T11:03:00Z",
    }
    for name in ("APP_VERSION", "GIT_COMMIT_SHA", "BUILD_DATE"):
        assert release_metadata({name: "secret text\n"}) == release_metadata({})


def test_liveness_survives_database_failure(monkeypatch):
    app = create_app({"TESTING": True})

    def unavailable():
        raise psycopg.OperationalError("a database detail that must stay private")

    monkeypatch.setattr(app.extensions["database"], "connect", unavailable)
    client = app.test_client()
    assert client.get("/health").status_code == 200
    assert client.get("/health/live").json == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 503 and ready.json["database"] == "unavailable"
    response = client.get("/api/tasks")
    assert response.status_code == 503
    assert response.json["error"]["code"] == "database_unavailable"
    assert "detail" not in response.text
    assert response.json["request_id"] == response.headers["X-Request-ID"]
    assert "taskops_database_available 0.0" in client.get("/metrics").text


def test_dashboard_and_safe_routing_errors():
    client = create_app({"TESTING": True}).test_client()
    index = client.get("/")
    assert index.status_code == 200
    assert b"TaskOps" in index.data and b"Add task" in index.data
    assert index.headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in index.headers["Content-Security-Policy"]
    untrusted = client.get("/health", headers={"Host": "stranger.example"})
    assert untrusted.status_code == 400 and "stranger.example" not in untrusted.text
    missing = client.get("/private-string")
    assert missing.status_code == 404 and "private-string" not in missing.text


def test_cross_origin_cannot_write():
    client = create_app({"TESTING": True}).test_client()
    assert client.post("/api/tasks", json={"title": "X"}, headers={
        "Origin": "https://other.example"
    }).status_code == 403
    assert client.delete("/api/tasks/1", headers={"Sec-Fetch-Site": "same-site"}).status_code == 403


def test_wrong_method_keeps_allow_header():
    response = create_app({"TESTING": True}).test_client().patch("/api/tasks")
    assert response.status_code == 405
    assert "POST" in response.headers["Allow"]
