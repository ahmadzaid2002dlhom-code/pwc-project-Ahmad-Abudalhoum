from fastapi import FastAPI

from app.config import settings


app = FastAPI()
app.state.settings = settings


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
