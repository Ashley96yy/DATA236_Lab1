from fastapi import FastAPI

app = FastAPI(title="Lab 2 User Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "user-service"}
