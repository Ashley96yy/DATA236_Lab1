from dataclasses import dataclass
import os


@dataclass
class ServiceSettings:
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/yelp_lab2")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")


def get_settings() -> ServiceSettings:
    return ServiceSettings()
