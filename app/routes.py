from flask import Blueprint, abort, current_app, g, render_template, request

bp = Blueprint("taskops", __name__)

STATUSES = ("pending", "in_progress", "completed")
PRIORITIES = ("low", "medium", "high")
FIELDS = {"title", "description", "status", "priority"}
TASK_COLUMNS = "id, title, description, status, priority, created_at, updated_at"


class ValidationError(ValueError):
    pass


def validate_task(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object.")
    if payload.keys() - FIELDS:
        raise ValidationError("Use only title, description, status, and priority.")

    text_fields = {}
    for field, limit in (("title", 120), ("description", 2000)):
        value = payload.get(field, "")
        if not isinstance(value, str) or any(
            character == "\x00" or 0xD800 <= ord(character) <= 0xDFFF for character in value
        ):
            raise ValidationError(f"{field.capitalize()} must be valid text.")
        value = value.strip()
        if len(value) > limit or (field == "title" and not value):
            raise ValidationError(
                "Title must contain 1–120 characters."
                if field == "title" else "Description must contain at most 2,000 characters."
            )
        text_fields[field] = value

    status = payload.get("status", "pending")
    priority = payload.get("priority", "medium")
    if status not in STATUSES:
        raise ValidationError("Status must be pending, in_progress, or completed.")
    if priority not in PRIORITIES:
        raise ValidationError("Priority must be low, medium, or high.")
    return text_fields["title"], text_fields["description"], status, priority


def database():
    return current_app.extensions["database"]


def task_json(row):
    for field in ("created_at", "updated_at"):
        row[field] = row[field].isoformat().replace("+00:00", "Z")
    return row


def require_task_id(task_id):
    if not 1 <= task_id <= 2_147_483_647:
        abort(404, "Task not found.")


@bp.get("/")
def index():
    return render_template("index.html", release=current_app.config["RELEASE"])


@bp.get("/api/tasks")
def tasks():
    statuses = request.args.getlist("status")
    if len(statuses) > 1 or (statuses and statuses[0] not in STATUSES):
        raise ValidationError("Filter by pending, in_progress, or completed.")
    if statuses:
        rows = database().query(
            f"SELECT {TASK_COLUMNS} FROM tasks WHERE status = %s ORDER BY id DESC",
            (statuses[0],),
        )
    else:
        rows = database().query(f"SELECT {TASK_COLUMNS} FROM tasks ORDER BY id DESC")
    return {"tasks": [task_json(row) for row in rows]}


@bp.post("/api/tasks")
def create_task():
    fields = validate_task(request.get_json())
    row = database().query(
        f"""INSERT INTO tasks (title, description, status, priority)
            VALUES (%s, %s, %s, %s) RETURNING {TASK_COLUMNS}""",
        fields, one=True,
    )
    current_app.extensions["metrics"].tasks_created.inc()
    return task_json(row), 201, {"Location": f"/api/tasks/{row['id']}"}


@bp.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    require_task_id(task_id)
    row = database().query(
        f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = %s", (task_id,), one=True
    )
    if row is None:
        abort(404, "Task not found.")
    return task_json(row)


@bp.put("/api/tasks/<int:task_id>")
def update_task(task_id):
    require_task_id(task_id)
    fields = validate_task(request.get_json())
    row = database().query(
        f"""UPDATE tasks SET title = %s, description = %s, status = %s, priority = %s,
            updated_at = GREATEST(updated_at, statement_timestamp())
            WHERE id = %s RETURNING {TASK_COLUMNS}""",
        (*fields, task_id), one=True,
    )
    if row is None:
        abort(404, "Task not found.")
    return task_json(row)


@bp.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    require_task_id(task_id)
    if database().query("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,), one=True) is None:
        abort(404, "Task not found.")
    return "", 204


@bp.get("/api/stats")
def stats():
    return database().query(
        """SELECT count(*) AS total,
            count(*) FILTER (WHERE status = 'pending') AS pending,
            count(*) FILTER (WHERE status = 'in_progress') AS in_progress,
            count(*) FILTER (WHERE status = 'completed') AS completed
            FROM tasks""",
        one=True,
    )


@bp.get("/health")
def health():
    return {**current_app.config["RELEASE"], "status": "ok"}


@bp.get("/health/live")
def live():
    return {"status": "ok"}


def probe_database():
    ready = database().ready()
    current_app.extensions["metrics"].database_available.set(int(ready))
    return ready


@bp.get("/health/ready")
def ready():
    if probe_database():
        return {"status": "ready", "database": "available"}
    g.error_kind = "database_unavailable"
    return {"status": "not_ready", "database": "unavailable"}, 503


@bp.get("/api/version")
def version():
    return current_app.config["RELEASE"]


@bp.get("/metrics")
def metrics():
    probe_database()
    return current_app.extensions["metrics"].response()
