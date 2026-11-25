"""AI Trip Optimizer — FastAPI application entry point.

Run from the backend/ directory:

    uvicorn app.main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.database.base import Base, SessionLocal, engine
# Imported for their side effect: registering the tables on Base.metadata
# before create_all() runs below.
from app.models import image_cache as _image_cache  # noqa: F401
from app.models import destination_cache as _destination_cache  # noqa: F401
from app.services.destination_service import seed_destinations

# Dev convenience: create tables on startup (use Alembic migrations in prod).
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_destinations(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AI Trip Optimizer API", version="0.1.0", lifespan=lifespan)
origins = [
    "https://ai-trip-optimizer-six.vercel.app",
    "http://localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Serve destination images from the frontend's public folder (dev convenience).
_IMAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "images")
)
if os.path.isdir(_IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=_IMAGES_DIR), name="images")
