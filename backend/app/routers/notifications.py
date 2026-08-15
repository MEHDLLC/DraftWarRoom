from fastapi import APIRouter, HTTPException, Query
from ..database import get_db
from ..schemas.models import NotificationInfo

router = APIRouter()


@router.get("/", response_model=list[NotificationInfo])
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get all notifications, optionally filtered to unread only."""
    db = await get_db()
    try:
        if unread_only:
            rows = await db.execute_fetchall(
                """
                SELECT id, title, body, type, priority, is_read, created_at
                FROM notification
                WHERE is_read = 0
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        else:
            rows = await db.execute_fetchall(
                """
                SELECT id, title, body, type, priority, is_read, created_at
                FROM notification
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        return [
            NotificationInfo(
                id=r["id"],
                title=r["title"],
                body=r["body"],
                type=r["type"],
                priority=r["priority"] or "normal",
                is_read=bool(r["is_read"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
    finally:
        await db.close()


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark a single notification as read."""
    db = await get_db()
    try:
        # Verify it exists
        rows = await db.execute_fetchall(
            "SELECT id FROM notification WHERE id = ?",
            (notification_id,),
        )
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notification_id} not found",
            )

        await db.execute(
            "UPDATE notification SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        await db.commit()
        return {"status": "ok", "notification_id": notification_id}
    finally:
        await db.close()


@router.get("/unread-count")
async def get_unread_count():
    """Get the count of unread notifications."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT COUNT(*) as count FROM notification WHERE is_read = 0"
        )
        count = rows[0]["count"] if rows else 0
        return {"unread_count": count}
    finally:
        await db.close()
