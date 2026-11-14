# ai-generated: 100% - OpenAI Copilot wrote positive and negative Semgrep tests for Lab 5 P-31
from datetime import datetime, timezone


def catches_parse_errors():
    # ruleid: broad-exception-handler
    try:
        return int("1")
    except Exception:
        return None


def catches_expected_error():
    # ok: broad-exception-handler
    try:
        return int("1")
    except ValueError:
        return None


def normalizes_naive_time(value: datetime):
    # ruleid: assume-utc-for-naive-time
    return value.replace(tzinfo=timezone.utc)


def rejects_ambiguous_time(value: datetime):
    if value.tzinfo is None:
        raise ValueError("timezone required")
    # ok: assume-utc-for-naive-time
    return value.astimezone(timezone.utc)


def deprecated_startup_hook():
    # ruleid: deprecated-fastapi-startup-hook
    @app.on_event("startup")
    def startup():
        return None


def supported_lifespan_alternative():
    # ok: deprecated-fastapi-startup-hook
    @app.get("/health")
    def health():
        return {"status": "ok"}
