from app import create_app

app = create_app()


if __name__ == "__main__":
    import os

    from app.observability import event

    event(app, "startup")
    try:
        app.run(host="127.0.0.1", port=int(os.environ.get("APP_PORT", "8090")))
    finally:
        event(app, "shutdown")
