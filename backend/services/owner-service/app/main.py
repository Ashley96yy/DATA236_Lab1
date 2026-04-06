from fastapi import FastAPI

app = FastAPI(title="Lab 2 Owner Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "owner-service"}
