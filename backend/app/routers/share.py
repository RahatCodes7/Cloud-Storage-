"""Public share link download endpoint."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import File, ShareLink, User
from app.telegram_client import download_file_from_telegram

router = APIRouter(tags=["share"])


@router.get("/s/{token}")
async def download_shared_file(token: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")
    if link.expires_at and datetime.utcnow() > link.expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link has expired")
    if link.max_downloads and link.download_count >= link.max_downloads:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Download limit reached")

    file_result = await db.execute(
        select(File).options(selectinload(File.owner)).where(File.id == link.file_id)
    )
    file = file_result.scalar_one_or_none()
    if not file or not file.owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    thread_id = file.owner.telegram_thread_id
    data = await download_file_from_telegram(file.telegram_message_id, thread_id)
    link.download_count += 1
    await db.commit()

    return Response(
        content=data,
        media_type=file.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file.display_name}"'},
    )
