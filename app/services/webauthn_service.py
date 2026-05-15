from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.models.credential import Credential
from app.repositories.user import user_repo
from app.repositories.credential import credential_repo
from app.utils.webauthn import get_registration_options, verify_registration, get_authentication_options, verify_authentication
from app.core.logging import logger
from typing import Any

class WebAuthnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def registration_options(self, user: User) -> dict:
        return get_registration_options(str(user.id), user.email)

    async def register_credential(self, user: User, response: Any):
        try:
            cred_id, pub_key, sign_count = verify_registration(str(user.id), response)
            
            await credential_repo.create(
                self.db,
                obj_in={
                    "user_id": user.id,
                    "auth_method": "webauthn",
                    "webauthn_credential_id": cred_id,
                    "webauthn_public_key": pub_key,
                    "webauthn_sign_count": sign_count
                }
            )
            return {"status": "success"}
        except Exception as e:
            logger.error(f"WebAuthn registration failed for user {user.id}", exc_info=True)
            raise HTTPException(status_code=400, detail="Registration failed")

    async def authentication_options(self, email: str) -> dict:
        user = await user_repo.get_by_email(self.db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return get_authentication_options(email)

    async def authenticate_credential(self, email: str, response: Any) -> User:
        user = await user_repo.get_by_email(self.db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        webauthn_creds = await credential_repo.get_all_by_user_id_and_method(self.db, user.id, "webauthn")
        
        if not credentials:
            raise HTTPException(status_code=400, detail="No passkeys found for user")
            
        # Normally match by credential_id, simplify for now
        cred = credentials[0]
        
        try:
            new_sign_count = verify_authentication(
                email, 
                response, 
                cred.webauthn_public_key, 
                cred.webauthn_sign_count or 0
            )
            
            cred.webauthn_sign_count = new_sign_count
            await self.db.commit()
            return user
        except Exception as e:
            logger.error(f"WebAuthn authentication failed for user {email}", exc_info=True)
            raise HTTPException(status_code=400, detail="Authentication failed")
