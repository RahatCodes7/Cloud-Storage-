"""Push/pull metadata JSON snapshots to/from Telegram control topic."""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session_maker
from app.models import User, File, ShareLink

logger = logging.getLogger(__name__)


def _serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def push_snapshot():
    """
    Push a full metadata snapshot to the Telegram control topic.
    Called after every write operation (upload, rename, delete, user-create).
    """
    from app.telegram_client import send_snapshot_to_telegram

    try:
        maker = get_session_maker()
        async with maker() as db:
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()

            files_result = await db.execute(select(File))
            files = files_result.scalars().all()

            snapshot = {
                "version": 1,
                "updated_at": datetime.utcnow().isoformat(),
                "users": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "password_hash": u.password_hash,
                        "is_admin": u.is_admin,
                        "telegram_thread_id": u.telegram_thread_id,
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                    }
                    for u in users
                ],
                "files": [
                    {
                        "id": f.id,
                        "owner_id": f.owner_id,
                        "telegram_message_id": f.telegram_message_id,
                        "display_name": f.display_name,
                        "original_filename": f.original_filename,
                        "mime_type": f.mime_type,
                        "size_bytes": f.size_bytes,
                        "folder_path": f.folder_path,
                        "is_trashed": f.is_trashed,
                        "trashed_at": f.trashed_at.isoformat() if f.trashed_at else None,
                        "created_at": f.created_at.isoformat() if f.created_at else None,
                        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                    }
                    for f in files
                ],
            }

        json_str = json.dumps(snapshot, default=_serialize_datetime, separators=(",", ":"))
        await send_snapshot_to_telegram(json_str)
        logger.info("Snapshot pushed to Telegram control topic")
    except Exception as e:
        logger.error(f"Failed to push snapshot: {e}")


async def retrieve_snapshot_data() -> Optional[dict]:
    """Pull the latest snapshot from Telegram."""
    from app.telegram_client import retrieve_snapshot_from_telegram

    try:
        json_str = await retrieve_snapshot_from_telegram()
        if json_str:
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to retrieve snapshot data: {e}")

    return None
