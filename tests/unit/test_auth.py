from typing import Generator
import pytest
from httpx import AsyncClient
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
