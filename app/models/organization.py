from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), index=True)
    
    users: Mapped[list["User"]] = relationship(back_populates="organization")
