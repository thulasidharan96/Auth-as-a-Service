from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.session import Session
from app.repositories.session import session_repo
from sqlalchemy import select

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionRead(BaseModel):
    id: UUID
    device_info: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime
    is_revoked: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SessionRead])
async def list_sessions(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Session).filter(Session.user_id == current_user.id))
    return list(result.scalars().all())

@router.delete("/{session_id}")
async def revoke_session_by_id(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    session = await session_repo.get(db, id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_revoked = True
    await db.commit()
    return {"status": "revoked"}
