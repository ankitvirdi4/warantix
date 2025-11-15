from fastapi import FastAPI

from .config import settings
from .core.logging import setup_logging
from .routers import analytics, auth, claims, clusters, ingest

setup_logging()

API_PREFIX = "/api/v1"


app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(ingest.router, prefix=API_PREFIX)
app.include_router(claims.router, prefix=API_PREFIX)
app.include_router(clusters.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok"}
