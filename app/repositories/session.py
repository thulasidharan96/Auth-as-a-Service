from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.repositories.base import BaseRepository
from app.models.session import Session

class SessionRepository(BaseRepository[Session]):
    async def get_by_refresh_token(self, db: AsyncSession, refresh_token: str) -> Optional[Session]:
        result = await db.execute(select(Session).filter(Session.refresh_token == refresh_token))
        return result.scalars().first()
    
    async def revoke_session(self, db: AsyncSession, refresh_token: str) -> None:
        await db.execute(
            update(Session)
            .where(Session.refresh_token == refresh_token)
            .values(is_revoked=True)
        )
        await db.commit()

session_repo = SessionRepository(Session)
