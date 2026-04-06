from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass
class ServiceSettings:
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "yelp_lab2")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET", "change-me"))
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))


@lru_cache(maxsize=1)
def get_settings() -> ServiceSettings:
    return ServiceSettings()
