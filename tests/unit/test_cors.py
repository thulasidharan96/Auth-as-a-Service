import os
import pytest
from pydantic import ValidationError

def test_cors_origins_prevent_asterisk():
    # Set the environment directly
    os.environ["SECRET_KEY"] = "foo"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = "postgres"
    os.environ["POSTGRES_DB"] = "postgres"

    # Valid config first so import succeeds
    os.environ["CORS_ORIGINS"] = "http://localhost:8000,http://localhost:3000"

    from app.core.config import Settings

    # Now explicitly test instantiation with invalid config
    os.environ["CORS_ORIGINS"] = "http://localhost:8000,*"
    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "CORS_ORIGINS cannot contain '*'" in str(exc_info.value)

    # Valid config test
    os.environ["CORS_ORIGINS"] = "http://localhost:8000,http://localhost:3000"
    settings = Settings()
    assert settings.CORS_ORIGINS == ["http://localhost:8000", "http://localhost:3000"]
