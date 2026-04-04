from datetime import timedelta, datetime, timezone
from jose import jwt
from app.core.config import settings

def create_magic_link_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "magic_link"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_magic_link_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "magic_link":
            return None
        return payload.get("sub")
    except Exception:
        return None
