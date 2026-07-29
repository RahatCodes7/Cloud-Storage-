"""Kurigram (Pyrogram fork) client lifecycle with retry/FloodWait wrapper."""

import asyncio
import io
import logging
import os
from typing import Optional

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from app.config import get_settings
from app.utils.retry import retry_on_flood

logger = logging.getLogger(__name__)

_client: Optional[Client] = None
_control_topic_id: Optional[int] = None


def get_telegram_client() -> Optional[Client]:
    return _client


def get_control_topic_id() -> Optional[int]:
    return _control_topic_id


async def init_telegram_client():
    """Initialize the Kurigram client from the session string on boot."""
    global _client, _control_topic_id

    settings = get_settings()
    if not settings.telegram_session_string:
        logger.warning("TELEGRAM_SESSION_STRING not set — Telegram features disabled")
        return

    _client = Client(
        name="trove",
        session_string=settings.telegram_session_string,
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        in_memory=True,  # Don't write .session files to disk
    )

    await _client.start()
    logger.info("Telegram client started successfully")

    # Create or find the control topic for snapshot storage
    await _ensure_control_topic()


async def _ensure_control_topic():
    """Create or find a dedicated control topic for metadata snapshots."""
    global _control_topic_id
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id
    if not chat_id:
        return

    try:
        async for topic in _client.get_forum_topics(chat_id):
            if topic.title == "__trove_control__":
                _control_topic_id = topic.id
                logger.info(f"Found control topic: {_control_topic_id}")
                return

        # Create control topic
        topic = await _client.create_forum_topic(chat_id, "__trove_control__")
        if hasattr(topic, 'id'):
            _control_topic_id = topic.id
        elif hasattr(topic, 'message_thread_id'):
            _control_topic_id = topic.message_thread_id
        logger.info(f"Created control topic: {_control_topic_id}")
    except Exception as e:
        logger.warning(f"Could not create/find control topic: {e}")


async def stop_telegram_client():
    global _client
    if _client:
        await _client.stop()
        _client = None
        logger.info("Telegram client stopped")


async def create_user_topic(user_id: str, username: str) -> int:
    """Create a forum topic for a new user. Returns the message_thread_id."""
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id
    if not _client or not chat_id:
        raise RuntimeError("Telegram client not available")

    topic_title = f"user_{username[:32]}"
    topic = await _client.create_forum_topic(chat_id, topic_title)
    if hasattr(topic, 'message_thread_id'):
        return topic.message_thread_id
    return topic.id


@retry_on_flood()
async def upload_file_to_telegram(
    user_thread_id: int,
    file_data: bytes,
    filename: str,
    mime_type: str,
    file_uuid: str,
    progress_callback=None,
) -> int:
    """Upload a file to the user's topic. Returns the message_id.

    Branches on MIME type to give Telegram inline previews:
    - image/*  → send_photo()  (inline image in Telegram)
    - video/*  → send_video()  (inline video player in Telegram)
    - audio/*  → send_audio()  (inline audio player in Telegram)
    - default  → send_document() (generic file)
    """
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id

    caption = f"UUID: {file_uuid}"

    # Use BytesIO to avoid writing temp files
    bio = io.BytesIO(file_data)
    bio.name = filename

    mime_lower = mime_type.lower()

    if mime_lower.startswith("image/"):
        msg: Message = await _client.send_photo(
            chat_id=chat_id,
            photo=bio,
            caption=caption,
            message_thread_id=user_thread_id,
            progress=progress_callback,
        )
    elif mime_lower.startswith("video/"):
        msg: Message = await _client.send_video(
            chat_id=chat_id,
            video=bio,
            caption=caption,
            message_thread_id=user_thread_id,
            supports_streaming=True,
            progress=progress_callback,
        )
    elif mime_lower.startswith("audio/"):
        msg: Message = await _client.send_audio(
            chat_id=chat_id,
            audio=bio,
            caption=caption,
            message_thread_id=user_thread_id,
            progress=progress_callback,
        )
    else:
        msg: Message = await _client.send_document(
            chat_id=chat_id,
            document=bio,
            caption=caption,
            message_thread_id=user_thread_id,
            force_document=True,
            progress=progress_callback,
        )

    return msg.id


async def download_file_from_telegram(message_id: int) -> bytes:
    """Download a file from Telegram by message reference. Returns bytes.

    Uses get_messages (without message_thread_id — messages in forum topics
    are uniquely identified by chat_id + message_id alone) to fetch the
    Message object, then downloads media by collecting streaming chunks.
    Uses stream_media() internally (same approach as preview) which is
    confirmed working.
    """
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id

    # Fetch the message object first with retry (same pattern as stream_file_from_telegram)
    msg = None
    for attempt in range(5):
        try:
            msg = await _client.get_messages(chat_id, message_id)
            break
        except FloodWait as e:
            wait = e.value if hasattr(e, 'value') else (e.x if hasattr(e, 'x') else 10)
            logger.warning(f"FloodWait getting message {message_id}: waiting {wait}s (attempt {attempt+1}/5)")
            await asyncio.sleep(wait)
        except Exception as e:
            if attempt == 4:
                raise
            delay = 1.0 * (2 ** attempt)
            logger.warning(f"Retryable error getting message {message_id}: {e}. Retrying in {delay}s")
            await asyncio.sleep(delay)

    if not msg or not msg.media:
        raise RuntimeError(f"No media found for message {message_id}")

    # Collect streaming chunks into a buffer (same stream_media approach as preview)
    bio = io.BytesIO()
    async for chunk in _client.stream_media(msg):
        bio.write(chunk)
    bio.seek(0)
    return bio.read()


async def stream_file_from_telegram(message_id: int):
    """
    Stream a file from Telegram in chunks without buffering the whole file in RAM.
    Uses Pyrogram's native stream_media() which yields chunks as they download.
    The message is found by chat_id + message_id alone (forum topics share the same chat).
    """
    if not _client:
        logger.error("Telegram client not available for streaming")
        return

    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id

    # Fetch the message with manual retry for FloodWait
    # (retry_on_flood decorator can't wrap async generators)
    # Note: get_messages doesn't accept message_thread_id — messages in
    # forum topics are uniquely identified by chat_id + message_id alone
    msg = None
    for attempt in range(5):
        try:
            msg = await _client.get_messages(chat_id, message_id)
            break
        except FloodWait as e:
            wait = e.value if hasattr(e, 'value') else (e.x if hasattr(e, 'x') else 10)
            logger.warning(f"FloodWait getting message {message_id}: waiting {wait}s (attempt {attempt+1}/5)")
            await asyncio.sleep(wait)
        except Exception as e:
            if attempt == 4:
                raise
            delay = 1.0 * (2 ** attempt)
            logger.warning(f"Retryable error getting message {message_id}: {e}. Retrying in {delay}s")
            await asyncio.sleep(delay)

    if not msg or not msg.media:
        logger.warning(f"No media found for message {message_id}")
        return

    # Stream media chunks directly from Telegram — no BytesIO buffer
    # stream_media() yields bytes chunks as they're downloaded
    async for chunk in _client.stream_media(msg):
        yield chunk


@retry_on_flood()
async def delete_telegram_message(message_id: int, user_thread_id: int):
    """Delete a message from Telegram."""
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id

    try:
        await _client.delete_messages(
            chat_id=chat_id,
            message_ids=message_id,
        )
    except Exception as e:
        logger.warning(f"Failed to delete Telegram message {message_id}: {e}")


@retry_on_flood()
async def send_snapshot_to_telegram(snapshot_json: str) -> int:
    """Push a metadata snapshot to the control topic. Returns the message_id."""
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id

    msg = await _client.send_message(
        chat_id=chat_id,
        text=f"SNAPSHOT\n{snapshot_json}",
        message_thread_id=_control_topic_id,
    )
    return msg.id


async def retrieve_snapshot_from_telegram() -> Optional[str]:
    """Retrieve the latest metadata snapshot from the control topic."""
    settings = get_settings()
    chat_id = settings.telegram_storage_chat_id
    if not _client or not chat_id or not _control_topic_id:
        return None

    try:
        async for msg in _client.get_chat_history(
            chat_id=chat_id,
            limit=20,
        ):
            if msg.message_thread_id != _control_topic_id:
                continue
            if msg.text and msg.text.startswith("SNAPSHOT\n"):
                return msg.text[len("SNAPSHOT\n"):]
    except Exception as e:
        logger.warning(f"Failed to retrieve snapshot: {e}")

    return None
