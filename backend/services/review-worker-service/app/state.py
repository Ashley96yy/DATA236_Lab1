from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock


_LOCK = Lock()
_STATE = {
    "processed_count": 0,
    "last_event": None,
    "last_error": None,
    "started_at": datetime.now(timezone.utc),
}


def record_processed(*, topic: str, payload: dict, result: dict) -> None:
    with _LOCK:
        _STATE["processed_count"] += 1
        _STATE["last_event"] = {
            "topic": topic,
            "payload": payload,
            "result": result,
            "processed_at": datetime.now(timezone.utc),
        }
        _STATE["last_error"] = None


def record_failure(*, topic: str, payload: dict, error: str) -> None:
    with _LOCK:
        _STATE["last_error"] = {
            "topic": topic,
            "payload": payload,
            "error": error,
            "failed_at": datetime.now(timezone.utc),
        }


def get_worker_status() -> dict:
    with _LOCK:
        return {
            "processed_count": _STATE["processed_count"],
            "last_event": _STATE["last_event"],
            "last_error": _STATE["last_error"],
            "started_at": _STATE["started_at"],
        }
