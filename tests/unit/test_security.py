import pytest
from unittest.mock import patch, ANY
from datetime import timedelta

from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.core.config import settings

def test_verify_password():
    with patch('app.utils.security.pwd_context.verify') as mock_verify:
        mock_verify.return_value = True
        assert verify_password("plain", "hash") is True
        mock_verify.assert_called_with("plain", "hash")

        mock_verify.return_value = False
        assert verify_password("wrong", "hash") is False
        mock_verify.assert_called_with("wrong", "hash")

def test_get_password_hash():
    with patch('app.utils.security.pwd_context.hash') as mock_hash:
        mock_hash.return_value = "hashed_pass"
        assert get_password_hash("plain") == "hashed_pass"
        mock_hash.assert_called_with("plain")

def test_create_access_token():
    with patch('app.utils.security.jwt.encode') as mock_encode:
        mock_encode.return_value = "mock_token"

        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        settings.SECRET_KEY = "test_secret"
        settings.ALGORITHM = "HS256"

        data = {"sub": "user123"}
        token = create_access_token(data)

        assert token == "mock_token"
        mock_encode.assert_called_with(
            ANY,
            "test_secret",
            algorithm="HS256"
        )

        called_data = mock_encode.call_args[0][0]
        assert called_data["sub"] == "user123"
        assert "exp" in called_data

def test_create_access_token_with_expires_delta():
    with patch('app.utils.security.jwt.encode') as mock_encode:
        settings.SECRET_KEY = "test_secret"
        settings.ALGORITHM = "HS256"

        mock_encode.return_value = "mock_token_custom_exp"

        data = {"sub": "user123"}
        delta = timedelta(minutes=15)

        token = create_access_token(data, expires_delta=delta)

        assert token == "mock_token_custom_exp"
        called_data = mock_encode.call_args[0][0]
        assert called_data["sub"] == "user123"
        assert "exp" in called_data

def test_create_refresh_token():
    with patch('app.utils.security.jwt.encode') as mock_encode:
        settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        settings.SECRET_KEY = "test_secret"
        settings.ALGORITHM = "HS256"

        mock_encode.return_value = "mock_refresh_token"

        token = create_refresh_token("user123")

        assert token == "mock_refresh_token"
        mock_encode.assert_called_with(
            ANY,
            "test_secret",
            algorithm="HS256"
        )

        called_data = mock_encode.call_args[0][0]
        assert called_data["sub"] == "user123"
        assert called_data["type"] == "refresh"
        assert "exp" in called_data

def test_create_refresh_token_with_expires_delta():
    with patch('app.utils.security.jwt.encode') as mock_encode:
        settings.SECRET_KEY = "test_secret"
        settings.ALGORITHM = "HS256"

        mock_encode.return_value = "mock_refresh_token_custom_exp"

        delta = timedelta(days=3)
        token = create_refresh_token("user123", expires_delta=delta)

        assert token == "mock_refresh_token_custom_exp"
        called_data = mock_encode.call_args[0][0]
        assert called_data["sub"] == "user123"
        assert called_data["type"] == "refresh"
        assert "exp" in called_data
