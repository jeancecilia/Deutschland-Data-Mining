from __future__ import annotations

import os
import socket
import time
from urllib.parse import urlparse

from sqlalchemy import create_engine, text

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    timeout_seconds = int(os.getenv("WAIT_TIMEOUT_SECONDS", "90"))
    retry_interval_seconds = float(os.getenv("WAIT_RETRY_INTERVAL_SECONDS", "2"))

    _wait_for_database(settings.database_url, timeout_seconds, retry_interval_seconds)
    _wait_for_tcp_service(settings.redis_url, timeout_seconds, retry_interval_seconds, "redis")


def _wait_for_database(database_url: str, timeout_seconds: int, retry_interval_seconds: float) -> None:
    started_at = time.monotonic()
    last_error: Exception | None = None

    while time.monotonic() - started_at < timeout_seconds:
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception as exc:  # pragma: no cover - startup guard
            last_error = exc
            time.sleep(retry_interval_seconds)

    raise RuntimeError(f"Database did not become ready within {timeout_seconds}s") from last_error


def _wait_for_tcp_service(url: str, timeout_seconds: int, retry_interval_seconds: float, label: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 0
    started_at = time.monotonic()
    last_error: Exception | None = None

    while time.monotonic() - started_at < timeout_seconds:
        try:
            with socket.create_connection((host, port), timeout=3):
                return
        except OSError as exc:  # pragma: no cover - startup guard
            last_error = exc
            time.sleep(retry_interval_seconds)

    raise RuntimeError(f"{label} did not become ready within {timeout_seconds}s") from last_error


if __name__ == "__main__":
    main()
