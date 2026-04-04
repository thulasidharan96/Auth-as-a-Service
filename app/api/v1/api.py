from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.sessions import router as session_router
from app.api.v1.apikeys import router as apikey_router

api_router = APIRouter()
api_router.include_router(auth_router.router)
api_router.include_router(session_router.router)
api_router.include_router(apikey_router.router)
