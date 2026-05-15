import pytest
from httpx import AsyncClient, ASGITransport
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from app.api.v1.auth.router import router as auth_router
from app.core.config import settings

class MockSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.scope["session"] = {}
        return await call_next(request)

# Do not name it test_app as Pytest thinks it's a test!
oauth_test_app = FastAPI()
oauth_test_app.add_middleware(MockSessionMiddleware)
oauth_test_app.include_router(auth_router)

@pytest.mark.asyncio
async def test_oauth_redirect_uri_no_host_header_injection():
    transport = ASGITransport(app=oauth_test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get(
            "/auth/login/google",
            headers={"Host": "attacker.com", "X-Forwarded-Host": "attacker.com"},
            follow_redirects=False
        )

    assert response.status_code == 302
    location = response.headers.get("Location")

    import urllib.parse
    parsed = urllib.parse.urlparse(location)
    query = urllib.parse.parse_qs(parsed.query)

    redirect_uri = query.get("redirect_uri", [""])[0]

    assert redirect_uri.startswith(settings.ORIGIN)
    assert "attacker.com" not in redirect_uri
