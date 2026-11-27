import json
import logging
import os
import sys
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

import psycopg
from flask import Response, abort, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    ProcessCollector,
    generate_latest,
)
from werkzeug.exceptions import HTTPException

from .routes import ValidationError

METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"}
MESSAGES = {
    400: "Malformed request.",
    403: "Cross-origin changes are blocked.",
    404: "Resource not found.",
    405: "Method not allowed.",
    413: "Request body exceeds 32 KiB.",
    415: "Send a request with Content-Type application/json.",
}


class Metrics:
    def __init__(self):
        self.registry = registry = CollectorRegistry()
        self.requests = Counter(
            "taskops_http_requests_total", "HTTP requests", ["method", "endpoint"], registry=registry
        )
        self.responses = Counter(
            "taskops_http_responses_total", "HTTP responses",
            ["method", "endpoint", "status"], registry=registry,
        )
        self.duration = Histogram(
            "taskops_http_request_duration_seconds", "HTTP request duration",
            ["method", "endpoint"], registry=registry,
        )
        self.errors = Counter(
            "taskops_application_errors_total", "Application errors",
            ["endpoint", "kind"], registry=registry,
        )
        self.database_available = Gauge(
            "taskops_database_available", "Whether PostgreSQL and the task schema are available",
            registry=registry,
        )
        self.tasks_created = Counter(
            "taskops_tasks_created_total", "Tasks created through the API", registry=registry
        )
        ProcessCollector(registry=registry)

    def response(self):
        return Response(generate_latest(self.registry), content_type=CONTENT_TYPE_LATEST)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created, timezone.utc)
        return json.dumps({
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "severity": record.levelname,
            "event": record.getMessage(),
            **record.fields,
        }, separators=(",", ":"))


def configure_logging(app):
    logger = logging.getLogger("taskops")
    logger.propagate = False
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level if level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO")
    if not logger.handlers:
        stdout = logging.StreamHandler(sys.stdout)
        stdout.addFilter(lambda record: record.levelno < logging.ERROR)
        stderr = logging.StreamHandler(sys.stderr)
        stderr.setLevel(logging.ERROR)
        for handler in (stdout, stderr):
            handler.setFormatter(JsonFormatter())
            logger.addHandler(handler)
    app.extensions["taskops_logger"] = logger


def event(app, name, level=logging.INFO, **fields):
    app.extensions["taskops_logger"].log(level, name, extra={
        "fields": {"app_version": app.config["RELEASE"]["version"], **fields}
    })


def install(app):
    configure_logging(app)
    metrics = app.extensions["metrics"] = Metrics()

    @app.before_request
    def start_request():
        g.started = perf_counter()
        g.request_id = uuid4().hex
        g.method = request.method if request.method in METHODS else "OTHER"
        rule = request.url_rule
        g.endpoint = ("<unmatched>" if rule is None
                      else "/static/<asset>" if rule.endpoint == "static" else rule.rule)
        if g.method in {"POST", "PUT", "DELETE"}:
            origin = request.headers.get("Origin")
            fetch_site = request.headers.get("Sec-Fetch-Site")
            if (origin is not None and origin != request.host_url.rstrip("/")) or fetch_site in {
                "cross-site", "same-site"
            }:
                abort(403)

    @app.after_request
    def finish_request(response):
        elapsed = perf_counter() - g.started
        method, endpoint, status = g.method, g.endpoint, response.status_code
        metrics.requests.labels(method, endpoint).inc()
        metrics.responses.labels(method, endpoint, str(status)).inc()
        metrics.duration.labels(method, endpoint).observe(elapsed)
        if status >= 400:
            metrics.errors.labels(endpoint, g.get("error_kind", f"http_{status}")).inc()

        response.headers.update({
            "X-Request-ID": g.request_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
                "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
            ),
        })
        if endpoint != "/static/<asset>":
            response.headers["Cache-Control"] = "no-store"
        level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
        event(app, "http_request", level, request_id=g.request_id, method=method,
              path=endpoint, status=status, duration_ms=round(elapsed * 1000, 3),
              error_kind=g.get("error_kind"))
        return response

    def error_response(code, kind, message):
        g.error_kind = kind
        return {"error": {"code": kind, "message": message}, "request_id": g.request_id}, code

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return error_response(400, "invalid_input", str(error))

    @app.errorhandler(HTTPException)
    def http_error(error):
        code = error.code or 500
        body, status = error_response(code, f"http_{code}", MESSAGES.get(code, "Request failed."))
        response = app.json.response(body)
        response.status_code = status
        if code == 405 and error.valid_methods:
            response.headers["Allow"] = ", ".join(error.valid_methods)
        return response

    @app.errorhandler(psycopg.Error)
    def database_error(_error):
        metrics.database_available.set(0)
        return error_response(503, "database_unavailable", "The task database is temporarily unavailable.")

    @app.errorhandler(Exception)
    def internal_error(_error):
        return error_response(500, "internal_error", "An unexpected application error occurred.")
