from datetime import timedelta
import pytest
from jose import jwt
from app.utils.security import create_access_token, create_refresh_token
from app.core.config import settings

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data=data)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

def test_create_access_token_with_expires_delta():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data=data, expires_delta=expires_delta)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

def test_create_refresh_token():
    subject = "testuser"
    token = create_refresh_token(subject=subject)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "testuser"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded

def test_create_refresh_token_with_expires_delta():
    subject = "testuser"
    expires_delta = timedelta(days=2)
    token = create_refresh_token(subject=subject, expires_delta=expires_delta)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "testuser"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded
