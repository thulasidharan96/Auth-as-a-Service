from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.credential import Credential

class CredentialRepository(BaseRepository[Credential]):
    async def get_by_user_id(self, db: AsyncSession, user_id: str, auth_method: Optional[str] = None) -> list[Credential]:
        stmt = select(Credential).filter(Credential.user_id == user_id)
        if auth_method:
            stmt = stmt.filter(Credential.auth_method == auth_method)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_method(self, db: AsyncSession, user_id: str, auth_method: str) -> Optional[Credential]:
        result = await db.execute(
            select(Credential).filter(
                Credential.user_id == user_id,
                Credential.auth_method == auth_method
            )
        )
        return result.scalars().first()

credential_repo = CredentialRepository(Credential)
