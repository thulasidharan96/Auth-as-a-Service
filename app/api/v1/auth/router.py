from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.user import UserCreate, UserRead, Token
from app.schemas.otp import OTPSetupResponse, OTPVerify
from app.schemas.webauthn import WebauthnRegistrationStart, WebauthnRegistrationFinish, WebauthnLoginStart, WebauthnLoginFinish
from app.services.auth import AuthService
from app.services.webauthn_service import WebAuthnService
from app.services.oauth_service import OAuthService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.utils.oauth import oauth

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, 
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    return await auth_service.register_user(user_in, request_ip=client_ip)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user = await auth_service.authenticate_user(form_data.username, form_data.password, request_ip=client_ip)
    
    user_agent = request.headers.get("user-agent")
    return await auth_service.create_session_tokens(user, device_info=user_agent, ip_address=client_ip)

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/magic-link")
async def request_magic_link(
    email: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    await auth_service.send_magic_link(email, request_ip=client_ip)
    return {"message": "If the email is registered, a magic link was sent."}

@router.post("/magic-login", response_model=Token)
async def login_with_magic_link(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    
    user = await auth_service.verify_magic_link(token, request_ip=client_ip)
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.create_session_tokens(user, device_info=user_agent, ip_address=client_ip)


@router.post("/setup-otp", response_model=OTPSetupResponse)
async def setup_otp(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    auth_service = AuthService(db)
    secret, uri = await auth_service.setup_otp(current_user)
    return OTPSetupResponse(secret=secret, uri=uri)

@router.post("/verify-otp")
async def verify_otp(
    otp_data: OTPVerify,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    auth_service = AuthService(db)
    await auth_service.verify_otp(current_user, otp_data.code)
    return {"message": "OTP verified successfully"}


@router.post("/webauthn/register/start")
async def webauthn_register_start(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = WebAuthnService(db)
    return await service.registration_options(current_user)

@router.post("/webauthn/register/finish")
async def webauthn_register_finish(
    data: WebauthnRegistrationFinish,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = WebAuthnService(db)
    return await service.register_credential(current_user, data.response)

@router.post("/webauthn/login/start")
async def webauthn_login_start(
    data: WebauthnLoginStart,
    db: AsyncSession = Depends(get_db_session)
):
    service = WebAuthnService(db)
    return await service.authentication_options(data.email)

@router.post("/webauthn/login/finish", response_model=Token)
async def webauthn_login_finish(
    data: WebauthnLoginFinish,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    service = WebAuthnService(db)
    user = await service.authenticate_credential(data.email, data.response)
    
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.create_session_tokens(user, device_info=user_agent, ip_address=client_ip)

from app.utils.oauth import oauth
from app.services.oauth_service import OAuthService
from fastapi.responses import RedirectResponse
from app.core.config import settings

@router.get("/login/{provider}")
async def login_via_provider(provider: str, request: Request):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported/configured")
        
    url_path = request.app.url_path_for('auth_via_provider', provider=provider)
    redirect_uri = f"{settings.ORIGIN.rstrip('/')}{url_path}"
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/callback/{provider}")
async def auth_via_provider(provider: str, request: Request, db: AsyncSession = Depends(get_db_session)):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")
        
    token = await client.authorize_access_token(request)
    
    if provider == 'google':
        user_info = token.get('userinfo')
    elif provider == 'github':
        resp = await client.get('user', token=token)
        user_info = resp.json()
        if not user_info.get("email"):
            # Fetch emails
            emails_resp = await client.get('user/emails', token=token)
            emails = emails_resp.json()
            primary_email = next((e['email'] for e in emails if e['primary']), None)
            user_info['email'] = primary_email

    else:
        user_info = {}
        
    oauth_service = OAuthService(db)
    client_ip = request.client.host if request.client else None
    user = await oauth_service.authenticate_oauth_user(provider, user_info, token.get('access_token'), request_ip=client_ip)
    
    auth_service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    
    tokens = await auth_service.create_session_tokens(user, device_info=user_agent, ip_address=client_ip)
    # Typically we redirect to frontend with tokens here in a real scenario
    return tokens

