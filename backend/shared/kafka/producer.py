from __future__ import annotations

import json

from shared.kafka.client import get_kafka_bootstrap_servers

try:
    from kafka import KafkaProducer
except Exception:  # pragma: no cover - optional at import time in dev
    KafkaProducer = None


def publish_message(topic: str, payload: dict) -> None:
    if KafkaProducer is None:
        raise RuntimeError("kafka-python is not installed or KafkaProducer could not be imported.")

    producer = KafkaProducer(
        bootstrap_servers=get_kafka_bootstrap_servers(),
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
    )
    try:
        future = producer.send(topic, payload)
        future.get(timeout=10)
    finally:
        producer.flush()
        producer.close()
