from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
import secrets
import hashlib
from datetime import datetime
from uuid import UUID

from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.api_key import APIKey

router = APIRouter(prefix="/apikeys", tags=["apikeys"])

class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = []

class APIKeyRead(BaseModel):
    id: UUID
    name: str
    scopes: List[str] | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyCreateResponse(APIKeyRead):
    raw_key: str

def generate_api_key() -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash

@router.post("/", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User does not belong to an organization")
        
    raw_key, key_hash = generate_api_key()
    
    new_key = APIKey(
        organization_id=current_user.organization_id,
        name=key_data.name,
        key_hash=key_hash,
        scopes=key_data.scopes
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # We must only return raw_key once
    response_data = APIKeyCreateResponse.model_validate(new_key, from_attributes=True)
    response_data.raw_key = raw_key
    return response_data

@router.get("/", response_model=List[APIKeyRead])
async def list_api_keys(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user.organization_id:
        return []
        
    result = await db.execute(select(APIKey).filter(APIKey.organization_id == current_user.organization_id))
    return list(result.scalars().all())

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User does not belong to an organization")
        
    result = await db.execute(select(APIKey).filter(APIKey.id == key_id, APIKey.organization_id == current_user.organization_id))
    key = result.scalars().first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    key.is_revoked = True
    await db.commit()
    return {"status": "revoked"}
