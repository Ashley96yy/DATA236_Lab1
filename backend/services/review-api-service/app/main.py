from fastapi import FastAPI

app = FastAPI(title="Lab 2 Review API Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "review-api-service"}
