from __future__ import annotations

import json
import logging
from typing import Callable

from shared.config.settings import get_settings
from shared.kafka.client import get_kafka_bootstrap_servers

try:
    from kafka import KafkaConsumer
except Exception:  # pragma: no cover
    KafkaConsumer = None

logger = logging.getLogger(__name__)


def start_consumer(topics: list[str], handler: Callable[[str, dict], dict]) -> None:
    """Blocks and loops infinitely to consume events and call handler."""
    if KafkaConsumer is None:
        raise RuntimeError("kafka-python is not installed or KafkaConsumer could not be imported.")

    settings = get_settings()
    group_id = getattr(settings, "kafka_review_consumer_group", "review-worker-group")

    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=get_kafka_bootstrap_servers(),
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    logger.info("Kafka consumer started listening to topics: %s", topics)
    try:
        for message in consumer:
            logger.info("Consumed event from %s: %s", message.topic, message.value)
            try:
                handler(message.topic, message.value)
                consumer.commit()
                logger.info(
                    "Committed Kafka offset for topic=%s partition=%s offset=%s",
                    message.topic,
                    message.partition,
                    message.offset,
                )
            except Exception as exc:
                logger.error("Failed to process event from %s: %s", message.topic, exc)
    finally:
        consumer.close()
