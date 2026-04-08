from __future__ import annotations

# Phase 2: structure only.
# Kafka consumer loop will be wired in Phase 4.
# No public HTTP routes here — health endpoint is in main.py.

from fastapi import APIRouter

router = APIRouter()
