from typing import Generator
import pytest
from httpx import AsyncClient
from fastapi import HTTPException

from app.main import app
from app.dependencies.auth import get_current_user

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mocker):
    # Mock the database session
    mock_db = mocker.AsyncMock()

    # Pass an invalid token to the dependency
    invalid_token = "invalid.token.string"

    # We expect an HTTPException with status_code 401
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=invalid_token, db=mock_db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
