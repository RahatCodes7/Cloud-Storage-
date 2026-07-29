"""SQLAlchemy async database setup with snapshot rebuild-on-boot."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session_maker


async def init_db():
    """Create all tables on boot."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    maker = get_session_maker()
    async with maker() as session:
        yield session


async def rebuild_from_snapshot(db: AsyncSession) -> bool:
    """
    Try to rebuild the local SQLite DB from a Telegram snapshot.
    Returns True if rebuild happened, False if local DB was already present.
    """
    from app.telegram_client import retrieve_snapshot_from_telegram
    from app.models import User, File
    from sqlalchemy import text

    # Check if DB already has data
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    if count and count > 0:
        logger.info("Local database already has data, skipping snapshot rebuild")
        return False

    try:
        raw = await retrieve_snapshot_from_telegram()
        if not raw:
            logger.info("No snapshot found in Telegram, starting fresh")
            return False

        snapshot_data = json.loads(raw)
        users_data = snapshot_data.get("users", [])
        files_data = snapshot_data.get("files", [])

        for u in users_data:
            user = User(
                id=u["id"],
                username=u["username"],
                password_hash=u.get("password_hash", ""),
                is_admin=u.get("is_admin", False),
                telegram_thread_id=u.get("telegram_thread_id", 0),
                created_at=datetime.fromisoformat(u["created_at"]) if u.get("created_at") else datetime.utcnow(),
            )
            db.add(user)

        for f in files_data:
            file = File(
                id=f["id"],
                owner_id=f["owner_id"],
                telegram_message_id=f.get("telegram_message_id", 0),
                display_name=f.get("display_name", f.get("original_filename", "")),
                original_filename=f.get("original_filename", ""),
                mime_type=f.get("mime_type", "application/octet-stream"),
                size_bytes=f.get("size_bytes", 0),
                folder_path=f.get("folder_path"),
                is_trashed=f.get("is_trashed", False),
                trashed_at=datetime.fromisoformat(f["trashed_at"]) if f.get("trashed_at") else None,
                created_at=datetime.fromisoformat(f["created_at"]) if f.get("created_at") else datetime.utcnow(),
                updated_at=datetime.fromisoformat(f["updated_at"]) if f.get("updated_at") else datetime.utcnow(),
            )
            db.add(file)

        await db.commit()
        logger.info(f"Rebuilt database from snapshot: {len(users_data)} users, {len(files_data)} files")
        return True
    except Exception as e:
        logger.error(f"Failed to rebuild from snapshot: {e}")
        await db.rollback()
        return False
