import os
import re

from flask import Flask

from .routes import bp


def release_metadata(environ):
    def value(name, pattern, default):
        raw = environ.get(name, "")
        return raw if re.fullmatch(pattern, raw) else default

    return {
        "name": "TaskOps",
        "version": value("APP_VERSION", r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]{1,40})?", "0.1.0"),
        "git_commit": value("GIT_COMMIT_SHA", r"[0-9a-fA-F]{7,64}", None),
        "build_date": value("BUILD_DATE", r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?", None),
    }


def create_app(config=None):
    app = Flask(__name__, static_url_path="/static")
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=32 * 1024,
        RELEASE=release_metadata(os.environ),
        TRUSTED_HOSTS=[
            host.strip()
            for host in os.environ.get("APP_TRUSTED_HOSTS", "localhost,127.0.0.1,[::1],app").split(",")
            if host.strip()
        ],
    )
    if config is not None:
        app.config.update(config)
    app.register_blueprint(bp)

    from .database import Database
    from .observability import install

    app.extensions["database"] = Database(app.config)
    install(app)
    return app
