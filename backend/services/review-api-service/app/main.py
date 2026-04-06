from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="Lab 2 Review API Service")

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "review-api-service"}
