import sys
import pytest
from unittest.mock import MagicMock, patch

def test_verify_authentication_no_challenge():
    """Test that verify_authentication raises an exception when no challenge is found."""
    # We patch sys.modules inside the test function or use unittest.mock.patch.dict
    # to avoid polluting global state for other test files.
    with patch.dict(sys.modules, {
        'webauthn': MagicMock(),
        'webauthn.helpers': MagicMock(),
        'webauthn.helpers.structs': MagicMock()
    }):
        # Mock settings
        settings_mock = MagicMock()
        settings_mock.RP_ID = "localhost"
        settings_mock.RP_NAME = "Auth Service"
        settings_mock.ORIGIN = "http://localhost"

        with patch.dict(sys.modules, {'app.core.config': MagicMock(settings=settings_mock)}):
            # Import after patching to ensure patched modules are used
            from app.utils.webauthn import verify_authentication, challenge_store

            # Ensure the challenge store does not contain the test email
            challenge_store.clear()

            with pytest.raises(Exception, match="Challenge not found"):
                verify_authentication(
                    email="test@example.com",
                    credential_response={},
                    public_key="00" * 32,
                    sign_count=0
                )
