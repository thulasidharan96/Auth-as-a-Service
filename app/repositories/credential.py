from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.credential import Credential

class CredentialRepository(BaseRepository[Credential]):
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> list[Credential]:
        result = await db.execute(select(Credential).filter(Credential.user_id == user_id))
        return list(result.scalars().all())

credential_repo = CredentialRepository(Credential)
