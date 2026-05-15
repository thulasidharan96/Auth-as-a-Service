import sys
from unittest.mock import MagicMock

# Mock dependencies that are missing in the environment to allow testing the logic
mock_modules = [
    "webauthn",
    "webauthn.helpers",
    "webauthn.helpers.structs",
    "pydantic_settings",
    "pydantic",
]

for mod in mock_modules:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

import pytest
# We also need to mock settings before importing utilities that use it
# or ensure the mock for pydantic_settings is enough.
# Since app.utils.webauthn does `from app.core.config import settings`,
# and app.core.config does `class Settings(BaseSettings):`,
# we should probably mock app.core.config if we don't want to deal with pydantic issues.

if "app.core.config" not in sys.modules:
    mock_config = MagicMock()
    mock_config.settings.RP_ID = "localhost"
    mock_config.settings.RP_NAME = "Auth as a Service"
    mock_config.settings.ORIGIN = "http://localhost:8000"
    sys.modules["app.core.config"] = mock_config

from app.utils.webauthn import verify_registration, verify_authentication, challenge_store

def test_verify_registration_missing_challenge():
    """
    🎯 What: Missing error test for WebAuthn verify_registration without challenge
    📊 Coverage: verify_registration raised Exception when challenge is not found
    """
    user_id = "test-user-id"
    # Ensure no challenge exists for this user
    if user_id in challenge_store:
        del challenge_store[user_id]

    with pytest.raises(Exception) as exc_info:
        verify_registration(user_id, MagicMock())

    assert str(exc_info.value) == "Challenge not found"

def test_verify_authentication_missing_challenge():
    """
    🎯 What: Missing error test for WebAuthn verify_authentication without challenge
    📊 Coverage: verify_authentication raised Exception when challenge is not found
    """
    email = "test@example.com"
    # Ensure no challenge exists for this email
    if email in challenge_store:
        del challenge_store[email]

    with pytest.raises(Exception) as exc_info:
        verify_authentication(email, MagicMock(), "public_key_hex", 0)

    assert str(exc_info.value) == "Challenge not found"
