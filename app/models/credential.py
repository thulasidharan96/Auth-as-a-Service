from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Credential(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "credentials"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    auth_method: Mapped[str] = mapped_column(String(50)) # password, passkey, otp (totp secret)
    
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Used for Email/Password
    webauthn_credential_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    webauthn_public_key: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Stored as hex/b64 string
    webauthn_sign_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="credentials")

class OAuthAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "oauth_accounts"
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True) # google, github
    provider_account_id: Mapped[str] = mapped_column(String(255), index=True)
    access_token: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
