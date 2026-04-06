from __future__ import annotations

from backend.shared.config.settings import get_settings


def get_kafka_bootstrap_servers() -> str:
    settings = get_settings()
    return settings.kafka_bootstrap_servers
