#!/usr/bin/env python3
"""One-time interactive login script to generate a Telegram session string."""
import asyncio
import os
import sys
from pathlib import Path

def load_env(dotenv_path: Path) -> dict:
    env = {}
    if dotenv_path.exists():
        with open(dotenv_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip("'").strip("'")
    return env

async def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    env_paths = [project_root / ".env", project_root / "backend" / ".env"]
    env_vars = {}
    for ep in env_paths:
        loaded = load_env(ep)
        env_vars.update(loaded)
        if loaded:
            print(f"Loaded .env from: {ep}")
    api_id = env_vars.get("TELEGRAM_API_ID") or os.environ.get("TELEGRAM_API_ID", "")
    api_hash = env_vars.get("TELEGRAM_API_HASH") or os.environ.get("TELEGRAM_API_HASH", "")
    if not api_id or not api_hash:
        print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH not found!")
        print("Create a .env file in the project root or backend/ folder")
        print("Get API creds from https://my.telegram.org/apps")
        sys.exit(1)
    try:
        api_id = int(api_id)
    except ValueError:
        print(f"ERROR: TELEGRAM_API_ID must be a number, got: {api_id}")
        sys.exit(1)
    print()
    print("='" * 30)
    print("Telegram Session String Generator")
    print("='" * 30)
    from pyrogram import Client
    print("Starting client...")
    client = Client("trove_gen", api_id=api_id, api_hash=api_hash, in_memory=True)
    async with client:
        print()
        print("V Connected to Telegram!")
        print()
        print("Your session string (SAVE THIS SECURELY):")
        print("-" * 60)
        session_string = await client.export_session_string()
        print(session_string)
        print("-" * 60)
        print()
        print("Add this to your .env file as:")
        print(f"  TELEGRAM_SESSION_STRING={session_string}")
        print()
        print("U26a0 Keep this string secret! It grants full access to your Telegram account.")

if __name__ == "__main__":
    asyncio.run(main())
