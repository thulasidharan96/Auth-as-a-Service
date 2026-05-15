import pytest
from unittest.mock import MagicMock, patch

import pyotp
from app.utils.otp import generate_totp_secret, get_totp_uri, verify_totp

@patch('app.utils.otp.pyotp')
def test_generate_totp_secret(mock_pyotp):
    mock_pyotp.random_base32.return_value = "JBSWY3DPEHPK3PXP"
    secret = generate_totp_secret()
    mock_pyotp.random_base32.assert_called_once()
    assert secret == "JBSWY3DPEHPK3PXP"

@patch('app.utils.otp.pyotp')
def test_get_totp_uri(mock_pyotp):
    secret = "JBSWY3DPEHPK3PXP"
    email = "test@example.com"
    issuer = "TestApp"

    mock_totp_instance = MagicMock()
    mock_totp_instance.provisioning_uri.return_value = "otpauth://totp/TestApp:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TestApp"
    mock_pyotp.totp.TOTP.return_value = mock_totp_instance

    uri = get_totp_uri(secret, email, issuer)

    mock_pyotp.totp.TOTP.assert_called_once_with(secret)
    mock_totp_instance.provisioning_uri.assert_called_once_with(name=email, issuer_name=issuer)
    assert uri == "otpauth://totp/TestApp:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TestApp"

@patch('app.utils.otp.pyotp')
def test_verify_totp_success(mock_pyotp):
    secret = "JBSWY3DPEHPK3PXP"
    code = "123456"

    mock_totp_instance = MagicMock()
    mock_totp_instance.verify.return_value = True
    mock_pyotp.TOTP.return_value = mock_totp_instance

    result = verify_totp(secret, code)

    mock_pyotp.TOTP.assert_called_once_with(secret)
    mock_totp_instance.verify.assert_called_once_with(code)
    assert result is True

@patch('app.utils.otp.pyotp')
def test_verify_totp_failure(mock_pyotp):
    secret = "JBSWY3DPEHPK3PXP"
    code = "000000"

    mock_totp_instance = MagicMock()
    mock_totp_instance.verify.return_value = False
    mock_pyotp.TOTP.return_value = mock_totp_instance

    result = verify_totp(secret, code)

    mock_pyotp.TOTP.assert_called_once_with(secret)
    mock_totp_instance.verify.assert_called_once_with(code)
    assert result is False
