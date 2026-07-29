"""Storage statistics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_session
from app.models import File, User

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
async def get_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    if not current_user.is_admin:
        r = await db.execute(
            select(func.count(), func.coalesce(func.sum(File.size_bytes), 0))
            .where(File.owner_id == current_user.id, File.is_trashed == False)
        )
        count, total = r.one()
        tr = await db.execute(
            select(File.mime_type, func.count(), func.coalesce(func.sum(File.size_bytes), 0))
            .where(File.owner_id == current_user.id, File.is_trashed == False)
            .group_by(File.mime_type)
        )
        by_type = [{"mime_type": row[0], "count": row[1], "size_bytes": row[2]} for row in tr.all()]
        return {"total_files": count, "total_bytes": total, "by_type": by_type}
    else:
        users_r = await db.execute(select(func.count()).select_from(User))
        files_r = await db.execute(
            select(func.count(), func.coalesce(func.sum(File.size_bytes), 0))
            .where(File.is_trashed == False)
        )
        fcount, ftotal = files_r.one()
        bur = await db.execute(
            select(User.username, func.count(File.id), func.coalesce(func.sum(File.size_bytes), 0))
            .outerjoin(File, File.owner_id == User.id).where(File.is_trashed == False).group_by(User.id)
        )
        by_user = [{"username": row[0], "count": row[1], "size_bytes": row[2]} for row in bur.all()]
        return {"total_users": users_r.scalar(), "total_files": fcount, "total_bytes": ftotal, "by_user": by_user}
