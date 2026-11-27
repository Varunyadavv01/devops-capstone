FROM python:3.13.18-slim-bookworm AS base

ARG APP_VERSION=0.1.0
ARG GIT_COMMIT_SHA=""
ARG BUILD_DATE=""
LABEL org.opencontainers.image.title="TaskOps" \
      org.opencontainers.image.version="$APP_VERSION" \
      org.opencontainers.image.revision="$GIT_COMMIT_SHA" \
      org.opencontainers.image.created="$BUILD_DATE"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_VERSION=$APP_VERSION \
    GIT_COMMIT_SHA=$GIT_COMMIT_SHA \
    BUILD_DATE=$BUILD_DATE

WORKDIR /opt/taskops
RUN groupadd --gid 10001 taskops \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin taskops

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt \
    && python -m pip check
COPY app/ app/
COPY migrations/ migrations/
COPY wsgi.py gunicorn.conf.py ./

FROM base AS test
COPY requirements-dev.txt .
RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements-dev.txt \
    && python -m pip check
COPY tests/ tests/
USER 10001:10001
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS runtime
USER 10001:10001
EXPOSE 8090
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8090/health/live', timeout=4).close()"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
