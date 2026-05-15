from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.schemas.user import UserCreate, Token
from app.models.user import User
from app.models.credential import Credential
from app.models.session import Session
from app.models.audit import AuditLog
from app.repositories.user import user_repo
from app.repositories.credential import credential_repo
from app.repositories.session import session_repo
from app.utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.config import settings

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_in: UserCreate, request_ip: Optional[str] = None) -> User:
        # Check if user exists
        existing_user = await user_repo.get_by_email(self.db, email=user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create User
        user_obj = await user_repo.create(self.db, obj_in={"email": user_in.email, "is_active": True})
        
        # Create Password Credential
        await credential_repo.create(
            self.db, 
            obj_in={
                "user_id": user_obj.id,
                "auth_method": "password",
                "password_hash": get_password_hash(user_in.password),
            }
        )
        
        # Log audit
        audit = AuditLog(user_id=user_obj.id, action="user_registered", ip_address=request_ip)
        self.db.add(audit)
        await self.db.commit()

        return user_obj

    async def send_magic_link(self, email: str, request_ip: Optional[str] = None):
        user = await user_repo.get_by_email(self.db, email)
        if not user:
            # We silently return or create a user in a real system based on policy.
            # For security against user-enumeration, we return silently.
            return True
            
        from app.utils.magic_link import create_magic_link_token
        token = create_magic_link_token(email)
        
        # Here we would send the email via Celery. For now, print it.
        # print(f"MAGIC LINK: {settings.ORIGIN}/auth/magic-login?token={token}")
        
        audit = AuditLog(user_id=user.id, action="magic_link_sent", ip_address=request_ip)
        self.db.add(audit)
        await self.db.commit()
        return True
        
    async def verify_magic_link(self, token: str, request_ip: Optional[str] = None) -> User:
        from app.utils.magic_link import verify_magic_link_token
        email = verify_magic_link_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired magic link")
            
        user = await user_repo.get_by_email(self.db, email)
        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="Invalid user")
            
        audit = AuditLog(user_id=user.id, action="login_magic_link_success", ip_address=request_ip)
        self.db.add(audit)
        await self.db.commit()
        return user
    async def authenticate_user(self, email: str, password: str, request_ip: Optional[str] = None) -> User:
        user = await user_repo.get_by_email(self.db, email)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        pwd_credential = await credential_repo.get_by_user_and_method(self.db, user.id, "password")
        
        if not pwd_credential or not pwd_credential.password_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if not verify_password(password, pwd_credential.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        # Log login
        audit = AuditLog(user_id=user.id, action="login_success", ip_address=request_ip)
        self.db.add(audit)
        await self.db.commit()

        return user
        
    async def create_session_tokens(self, user: User, device_info: Optional[str] = None, ip_address: Optional[str] = None) -> Token:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # Store refresh token in session
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await session_repo.create(
            self.db,
            obj_in={
                "user_id": user.id,
                "refresh_token": refresh_token,
                "device_info": device_info,
                "ip_address": ip_address,
                "expires_at": expires_at,
                "is_revoked": False
            }
        )
        
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def setup_otp(self, user: User) -> tuple[str, str]:
        from app.utils.otp import generate_totp_secret, get_totp_uri
        
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, user.email, settings.RP_NAME)
        
        # Save to DB
        await credential_repo.create(
            self.db,
            obj_in={
                "user_id": user.id,
                "auth_method": "otp",
                "totp_secret": secret
            }
        )
        return secret, uri

    async def verify_otp(self, user: User, code: str) -> bool:
        otp_cred = await credential_repo.get_by_user_and_method(self.db, user.id, "otp")
        
        if not otp_cred or not otp_cred.totp_secret:
            raise HTTPException(status_code=400, detail="OTP not set up")
            
        from app.utils.otp import verify_totp
        if not verify_totp(otp_cred.totp_secret, code):
            raise HTTPException(status_code=400, detail="Invalid OTP code")
            
        return True
