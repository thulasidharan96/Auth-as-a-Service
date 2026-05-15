import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from app.services.webauthn_service import WebAuthnService
from app.models.user import User

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session

@pytest.fixture
def webauthn_service(mock_db_session):
    return WebAuthnService(db=mock_db_session)

@pytest.fixture
def mock_user():
    user = User(
        id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com"
    )
    return user

@pytest.mark.asyncio
async def test_register_credential_generic_error(webauthn_service, mock_user):
    # Mock verify_registration to raise an exception
    with patch("app.services.webauthn_service.verify_registration", side_effect=Exception("Secret traceback detail that shouldn't be leaked")):
        with pytest.raises(HTTPException) as exc_info:
            await webauthn_service.register_credential(mock_user, response={})

        # Check that the exception message is generic
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Registration failed"

@pytest.mark.asyncio
async def test_authenticate_credential_generic_error(webauthn_service, mock_user):
    # Setup mocks
    with patch("app.services.webauthn_service.user_repo.get_by_email", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.webauthn_service.credential_repo.get_by_user_id", new_callable=AsyncMock) as mock_get_creds, \
         patch("app.services.webauthn_service.verify_authentication", side_effect=Exception("Another secret traceback")):

        mock_get_user.return_value = mock_user
        mock_cred = MagicMock()
        mock_cred.auth_method = "webauthn"
        mock_cred.webauthn_public_key = b"public_key"
        mock_cred.webauthn_sign_count = 0
        mock_get_creds.return_value = [mock_cred]

        with pytest.raises(HTTPException) as exc_info:
            await webauthn_service.authenticate_credential(mock_user.email, response={})

        # Check that the exception message is generic
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Authentication failed"
