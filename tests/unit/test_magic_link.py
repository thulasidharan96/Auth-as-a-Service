from datetime import datetime, timezone, timedelta
from jose import jwt
from app.utils.magic_link import create_magic_link_token, verify_magic_link_token
from app.core.config import settings

def test_create_magic_link_token():
    email = "test@example.com"
    token = create_magic_link_token(email)

    # Verify it's a valid JWT by attempting to decode it with the same settings
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == email
    assert payload["type"] == "magic_link"
    assert "exp" in payload

    # Check expiration is roughly 15 minutes from now
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Allow a small margin of error for test execution time
    assert abs((exp_time - expected_exp).total_seconds()) < 60

def test_verify_magic_link_token_valid():
    email = "test@example.com"
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "magic_link"}

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    result = verify_magic_link_token(token)
    assert result == email

def test_verify_magic_link_token_invalid_type():
    email = "test@example.com"
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}  # Wrong type

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    result = verify_magic_link_token(token)
    assert result is None

def test_verify_magic_link_token_expired():
    email = "test@example.com"
    expire = datetime.now(timezone.utc) - timedelta(minutes=15)  # Expired
    to_encode = {"exp": expire, "sub": email, "type": "magic_link"}

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    result = verify_magic_link_token(token)
    assert result is None

def test_verify_magic_link_token_invalid_signature():
    email = "test@example.com"
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "magic_link"}

    # Encode with a different secret key
    token = jwt.encode(to_encode, "wrong_secret_key", algorithm=settings.ALGORITHM)

    result = verify_magic_link_token(token)
    assert result is None

def test_verify_magic_link_token_malformed():
    result = verify_magic_link_token("not.a.valid_token")
    assert result is None
