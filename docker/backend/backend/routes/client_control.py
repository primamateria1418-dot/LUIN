"""
LUIN Dynamic Client Control Sync
Handles live client adjustments for posting times, brand messaging, frequency
and syncs them to n8n workflows and the database.
"""

import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from config import get_settings
from middleware.auth import get_current_user_token
from database import async_session_maker, Client
from sqlalchemy import select

logger = logging.getLogger("luin.client_control")
router = APIRouter()
settings = get_settings()

class ClientControlUpdate(BaseModel):
    client_id: str = Field(..., description="Client workspace ID")
    posting_schedule: Optional[List[dict]] = Field(None, description="Array of {day: 'mon', time: '09:00', platform: 'twitter'}")
    brand_voice: Optional[str] = Field(None, description="Updated brand voice/tone description")
    content_frequency: Optional[str] = Field(None, description="Daily, weekly, bi-weekly, monthly")
    key_messages: Optional[List[str]] = Field(None, description="Array of key brand messages")
    target_audience: Optional[dict] = Field(None, description="Demographic target {age_range, interests, location}")
    n8n_webhook_url: Optional[str] = Field(None, description="Override n8n webhook URL")

class ClientControlResponse(BaseModel):
    client_id: str
    status: str
    message: str
    synced_to_n8n: bool
    updated_fields: List[str]

@router.post("/client-control/sync", response_model=ClientControlResponse)
async def sync_client_control(update: ClientControlUpdate, user_token: dict = Depends(get_current_user_token)):
    """
    Sync client campaign and media studio settings to FastAPI and n8n.
    Allows live adjustments to posting times, brand messaging, and frequency.
    """
    # Validate client exists
    async with async_session_maker() as session:
        result = await session.execute(select(Client).where(Client.id == update.client_id))
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client workspace not found")
    
    updated_fields = []
    synced_to_n8n = False
    
    # Update database
    async with async_session_maker() as session:
        if update.posting_schedule:
            await session.execute(
                Client.__table__.update()
                .where(Client.id == update.client_id)
                .values(posting_schedule=update.posting_schedule)
            )
            updated_fields.append("posting_schedule")
        
        if update.brand_voice:
            await session.execute(
                Client.__table__.update()
                .where(Client.id == update.client_id)
                .values(brand_voice=update.brand_voice)
            )
            updated_fields.append("brand_voice")
        
        if update.content_frequency:
            await session.execute(
                Client.__table__.update()
                .where(Client.id == update.client_id)
                .values(content_frequency=update.content_frequency)
            )
            updated_fields.append("content_frequency")
        
        if update.key_messages:
            await session.execute(
                Client.__table__.update()
                .where(Client.id == update.client_id)
                .values(key_messages=update.key_messages)
            )
            updated_fields.append("key_messages")
        
        if update.target_audience:
            await session.execute(
                Client.__table__.update()
                .where(Client.id == update.client_id)
                .values(target_audience=update.target_audience)
            )
            updated_fields.append("target_audience")
        
        await session.commit()
    
    # Sync to n8n via webhook
    n8n_url = update.n8n_webhook_url or settings.N8N_WEBHOOK_URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{n8n_url}/client-control-sync",
                json={
                    "client_id": update.client_id,
                    "updates": {k: v for k, v in update.dict().items() if v is not None},
                    "timestamp": "now"
                }
            )
            if response.status_code == 200:
                synced_to_n8n = True
                logger.info(f"Client control synced to n8n for {update.client_id}")
            else:
                logger.warning(f"n8n sync failed for {update.client_id}: {response.status_code}")
    except Exception as e:
        logger.error(f"n8n sync error for {update.client_id}: {str(e)}")
    
    return ClientControlResponse(
        client_id=update.client_id,
        status="success",
        message=f"Updated {len(updated_fields)} fields",
        synced_to_n8n=synced_to_n8n,
        updated_fields=updated_fields
    )

@router.get("/client-control/{client_id}")
async def get_client_control(client_id: str, user_token: dict = Depends(get_current_user_token)):
    """Get current client control settings."""
    async with async_session_maker() as session:
        result = await session.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client workspace not found")
        
        return {
            "client_id": str(client.id),
            "posting_schedule": client.posting_schedule or [],
            "brand_voice": client.brand_voice or "",
            "content_frequency": client.content_frequency or "",
            "key_messages": client.key_messages or [],
            "target_audience": client.target_audience or {},
        }
