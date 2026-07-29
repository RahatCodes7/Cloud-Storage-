"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import init_db, get_session_maker, rebuild_from_snapshot
from app.telegram_client import init_telegram_client, stop_telegram_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Trove...")
    await init_db()
    await init_telegram_client()
    maker = get_session_maker()
    async with maker() as db:
        await rebuild_from_snapshot(db)
    logger.info("Trove started")
    yield
    await stop_telegram_client()
    logger.info("Trove stopped")

app = FastAPI(title="Trove", version="1.0.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from app.routers import auth, files, share, stats
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(share.router)
app.include_router(stats.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Trove", "version": "1.0.0"}

try:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")
    logger.info("Frontend static files mounted")
except Exception as e:
    logger.info(f"No frontend build found, API only: {e}")
