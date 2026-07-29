"""File CRUD endpoints."""
import io
import logging
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import File, User, ShareLink
from app.telegram_client import (
    stream_file_from_telegram,
    upload_file_to_telegram,
    download_file_from_telegram,
    delete_telegram_message,
)
from app.utils.snapshot import push_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["files"])


class FileResponse(BaseModel):
    id: str
    display_name: str
    original_filename: str
    mime_type: str
    size_bytes: int
    folder_path: Optional[str] = None
    is_trashed: bool = False
    trashed_at: Optional[str] = None
    created_at: str
    updated_at: str


class UpdateFileRequest(BaseModel):
    display_name: Optional[str] = None
    folder_path: Optional[str] = None


@router.get("", response_model=list[FileResponse])
async def list_files(
    q: Optional[str] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    folder: Optional[str] = Query(None),
    sort: str = Query("created_at"),
    trashed: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    query = select(File).where(
        File.owner_id == current_user.id, File.is_trashed == trashed
    )
    if q:
        query = query.where(File.display_name.ilike(f"%{q}%"))
    if type:
        query = query.where(File.mime_type.ilike(f"%{type}%"))
    if folder is not None:
        query = query.where(File.folder_path == folder)
    elif not trashed:
        query = query.where(File.folder_path.is_(None))
    sort_col = getattr(File, sort, File.created_at)
    query = query.order_by(sort_col.desc())
    result = await db.execute(query)
    files = result.scalars().all()
    return [
        FileResponse(
            id=f.id,
            display_name=f.display_name,
            original_filename=f.original_filename,
            mime_type=f.mime_type,
            size_bytes=f.size_bytes,
            folder_path=f.folder_path,
            is_trashed=f.is_trashed,
            trashed_at=f.trashed_at.isoformat() if f.trashed_at else None,
            created_at=f.created_at.isoformat() if f.created_at else None,
            updated_at=f.updated_at.isoformat() if f.updated_at else None,
        )
        for f in files
    ]


@router.post("", response_model=FileResponse)
async def upload_file(
    file: UploadFile,
    folder_path: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    from app.config import get_settings

    settings = get_settings()
    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )
    file_uuid = str(uuid.uuid4())
    file_id = await upload_file_to_telegram(
        user_thread_id=current_user.telegram_thread_id,
        file_data=data,
        filename=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
        file_uuid=file_uuid,
    )
    db_file = File(
        id=file_uuid,
        owner_id=current_user.id,
        telegram_message_id=file_id,
        display_name=file.filename or "unnamed",
        original_filename=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        folder_path=folder_path,
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    await push_snapshot()
    return FileResponse(
        id=db_file.id,
        display_name=db_file.display_name,
        original_filename=db_file.original_filename,
        mime_type=db_file.mime_type,
        size_bytes=db_file.size_bytes,
        folder_path=db_file.folder_path,
        is_trashed=db_file.is_trashed,
        trashed_at=db_file.trashed_at.isoformat() if db_file.trashed_at else None,
        created_at=db_file.created_at.isoformat() if db_file.created_at else None,
        updated_at=db_file.updated_at.isoformat() if db_file.updated_at else None,
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.size_bytes < 50 * 1024 * 1024:
        data = await download_file_from_telegram(
            file.telegram_message_id
        )
        return Response(
            content=data,
            media_type=file.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file.display_name}"',
                "Content-Length": str(len(data)),
            },
        )

    async def stream():
        async for chunk in stream_file_from_telegram(file.telegram_message_id):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type=file.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file.display_name}"'},
    )


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    async def stream():
        async for chunk in stream_file_from_telegram(file.telegram_message_id):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type=file.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{file.display_name}"',
            "Accept-Ranges": "bytes",
        },
    )


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: str,
    req: UpdateFileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if req.display_name is not None:
        file.display_name = req.display_name
    if req.folder_path is not None:
        file.folder_path = req.folder_path if req.folder_path else None
    await db.commit()
    await db.refresh(file)
    await push_snapshot()
    return FileResponse(
        id=file.id,
        display_name=file.display_name,
        original_filename=file.original_filename,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        folder_path=file.folder_path,
        is_trashed=file.is_trashed,
        trashed_at=file.trashed_at.isoformat() if file.trashed_at else None,
        created_at=file.created_at.isoformat() if file.created_at else None,
        updated_at=file.updated_at.isoformat() if file.updated_at else None,
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.is_trashed = True
    file.trashed_at = datetime.utcnow()
    await db.commit()
    await push_snapshot()
    return {"ok": True}


@router.delete("/{file_id}/permanent")
async def permanent_delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Permanently delete a file — removes from Telegram AND the database."""
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from Telegram first (best effort — proceed even if it fails)
    if file.telegram_message_id:
        try:
            await delete_telegram_message(file.telegram_message_id, current_user.telegram_thread_id)
        except Exception as e:
            logger.warning(f"Failed to delete Telegram message {file.telegram_message_id}: {e}")

    # Delete associated share links first
    await db.execute(
        sa_delete(ShareLink).where(ShareLink.file_id == file.id)
    )
    # Delete the file record
    await db.delete(file)
    await db.commit()
    await push_snapshot()
    return {"ok": True}


@router.post("/{file_id}/restore", response_model=FileResponse)
async def restore_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.owner_id == current_user.id,
            File.is_trashed == True,
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.is_trashed = False
    file.trashed_at = None
    await db.commit()
    await db.refresh(file)
    await push_snapshot()
    return FileResponse(
        id=file.id,
        display_name=file.display_name,
        original_filename=file.original_filename,
        mime_type=file.mime_type,
        size_bytes=file.size_bytes,
        folder_path=file.folder_path,
        is_trashed=file.is_trashed,
        trashed_at=None,
        created_at=file.created_at.isoformat() if file.created_at else None,
        updated_at=file.updated_at.isoformat() if file.updated_at else None,
    )


@router.post("/{file_id}/share")
async def create_share_link(
    file_id: str,
    expires_in_hours: Optional[int] = Query(None),
    max_downloads: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.owner_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    token = secrets.token_urlsafe(32)
    link = ShareLink(
        file_id=file.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        if expires_in_hours
        else None,
        max_downloads=max_downloads,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return {
        "token": token,
        "url": f"/s/{token}",
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "max_downloads": link.max_downloads,
    }
