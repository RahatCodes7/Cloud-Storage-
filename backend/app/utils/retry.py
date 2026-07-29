"""Retry/backoff helpers for Telegram API calls, handling FloodWait."""

import asyncio
import logging
from functools import wraps

from pyrogram.errors import FloodWait, RPCError

logger = logging.getLogger(__name__)


def retry_on_flood(max_retries: int = 5, base_delay: float = 1.0):
    """
    Decorator that catches FloodWait errors and retries after the required wait.
    Also applies exponential backoff for connection-level network errors.

    Deterministic API errors (RPCError) are raised immediately — only
    transient network errors (connection drops, timeouts) and FloodWait
    are retried.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except FloodWait as e:
                    wait_seconds = e.value if hasattr(e, 'value') else (e.x if hasattr(e, 'x') else 10)
                    logger.warning(f"FloodWait on {func.__name__}: waiting {wait_seconds}s (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(wait_seconds)
                    last_exception = e
                except RPCError:
                    # Deterministic API errors (CHANNEL_INVALID, PEER_ID_INVALID, etc.)
                    # should fail fast, not retry — retrying won't fix them
                    raise
                except (OSError, ConnectionError, asyncio.TimeoutError) as e:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Network error on {func.__name__}: {e}. Retrying in {delay}s (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(delay)
                    last_exception = e
                except Exception as e:
                    # Unknown errors: retry with backoff, but let one more
                    # specific handler catch them next time
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retryable error on {func.__name__}: {e}. Retrying in {delay}s (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(delay)
                    last_exception = e

            if last_exception:
                raise last_exception
        return wrapper
    return decorator
