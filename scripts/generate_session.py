"""One-time script to generate a Telegram session string."""
import asyncio
import os
from pyrogram import Client

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID") or input("TELEGRAM_API_ID: "))
    api_hash = os.getenv("TELEGRAM_API_HASH") or input("TELEGRAM_API_HASH: ")
    print("
Starting Telegram client... You will need phone + OTP.")
    async with Client("trove_gen", api_id=api_id, api_hash=api_hash) as app:
        s = await app.export_session_string()
        print("
" + "="*60)
        print("SESSION STRING (save as TELEGRAM_SESSION_STRING):")
        print("="*60)
        print(s)
        print("="*60)
        print("
TREAT THIS LIKE A PASSWORD - never commit it!")

if __name__ == "__main__":
    asyncio.run(main())
