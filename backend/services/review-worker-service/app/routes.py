from fastapi import APIRouter
from app.state import get_worker_status

router = APIRouter()


@router.get("/worker/status")
def worker_status() -> dict:
    return get_worker_status()
