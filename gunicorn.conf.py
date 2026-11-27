# A single synchronous worker keeps the Prometheus registry process-local.
bind = "0.0.0.0:8090"
workers = 1
worker_class = "sync"
timeout = 15
graceful_timeout = 15
accesslog = None
errorlog = "-"
limit_request_line = 4094
limit_request_fields = 50
limit_request_field_size = 4096


def post_worker_init(worker):
    from app.observability import event

    event(worker.wsgi, "startup")


def worker_exit(server, worker):
    from app.observability import event

    if worker.wsgi is not None:
        event(worker.wsgi, "shutdown")
