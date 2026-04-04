from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.user import User
from app.models.credential import OAuthAccount
from app.models.audit import AuditLog
from app.repositories.user import user_repo

class OAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_oauth_user(self, provider: str, user_info: dict, access_token: str, request_ip: Optional[str] = None) -> User:
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth service")

        # 1. See if the user exists
        user = await user_repo.get_by_email(self.db, email)
        
        if not user:
            # Create user implicitly
            user = await user_repo.create(self.db, obj_in={"email": email, "is_active": True, "is_verified": True})
            audit = AuditLog(user_id=user.id, action="user_registered_oauth", ip_address=request_ip)
            self.db.add(audit)
            
        provider_account_id = str(user_info.get("sub") or user_info.get("id"))
        
        # 2. See if the oauth account exists
        result = await self.db.execute(
            select(OAuthAccount).filter(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == provider,
                OAuthAccount.provider_account_id == provider_account_id
            )
        )
        oauth_account = result.scalars().first()
        
        if oauth_account:
            oauth_account.access_token = access_token
        else:
            new_oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_account_id=provider_account_id,
                access_token=access_token
            )
            self.db.add(new_oauth_account)
            
        # Log login
        audit = AuditLog(user_id=user.id, action=f"login_{provider}_success", ip_address=request_ip)
        self.db.add(audit)
        await self.db.commit()

        return user
