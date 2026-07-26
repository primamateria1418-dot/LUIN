"""
LUIN Client Campaign & Media Studio
Handles campaign submissions, media generation, and asset management.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from config import get_settings
from middleware.auth import get_current_user_token
from database import async_session_maker, Client, CampaignQueue
from sqlalchemy import select

logger = logging.getLogger("luin.campaign_studio")
router = APIRouter()
settings = get_settings()

class CampaignSubmission(BaseModel):
    client_id: str
    campaign_name: str
    campaign_description: str
    target_platforms: List[str]
    key_messages: List[str]
    media_types: List[str]  # image, video, copy, carousel, reel
    brand_voice: Optional[str] = None
    posting_schedule: Optional[List[dict]] = None
    content_frequency: Optional[str] = None
    target_audience: Optional[dict] = None

class CampaignResponse(BaseModel):
    id: str
    client_id: str
    name: str
    description: str
    status: str
    platforms: List[str]
    media_types: List[str]
    key_messages: List[str]
    created_at: str

@router.post("/campaign-studio/submit", response_model=CampaignResponse)
async def submit_campaign(submission: CampaignSubmission, user_token: dict = Depends(get_current_user_token)):
    """Submit a new marketing campaign for generation."""
    async with async_session_maker() as session:
        # Validate client
        result = await session.execute(select(Client).where(Client.id == submission.client_id))
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client workspace not found")
        
        # Create campaign entry
        campaign = CampaignQueue(
            client_id=submission.client_id,
            platform="multi",
            content_type="campaign",
            draft_text=submission.campaign_description,
            status="pending",
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        
        return CampaignResponse(
            id=str(campaign.id),
            client_id=submission.client_id,
            name=submission.campaign_name,
            description=submission.campaign_description,
            status="pending",
            platforms=submission.target_platforms,
            media_types=submission.media_types,
            key_messages=submission.key_messages,
            created_at=str(campaign.created_at),
        )

@router.get("/campaign-studio/{client_id}")
async def get_campaigns(client_id: str, user_token: dict = Depends(get_current_user_token)):
    """Get all campaigns for a client."""
    async with async_session_maker() as session:
        result = await session.execute(select(CampaignQueue).where(CampaignQueue.client_id == client_id))
        campaigns = result.scalars().all()
        return [
            CampaignResponse(
                id=str(c.id),
                client_id=str(c.client_id),
                name=c.draft_text[:50] + "..." if c.draft_text else "",
                description=c.draft_text or "",
                status=c.status.value if hasattr(c.status, 'value') else str(c.status),
                platforms=[],
                media_types=[],
                key_messages=[],
                created_at=str(c.created_at),
            ) for c in campaigns
        ]

@router.post("/campaign-studio/{campaign_id}/generate-media")
async def generate_media(campaign_id: str, user_token: dict = Depends(get_current_user_token)):
    """Trigger media generation for a campaign."""
    async with async_session_maker() as session:
        result = await session.execute(select(CampaignQueue).where(CampaignQueue.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Trigger n8n workflow for media generation
        n8n_url = settings.N8N_WEBHOOK_URL
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{n8n_url}/campaign-media-gen",
                    json={"campaign_id": str(campaign.id), "client_id": str(campaign.client_id)}
                )
                if response.status_code == 200:
                    return {"status": "media_generation_triggered", "campaign_id": str(campaign.id)}
                else:
                    raise HTTPException(status_code=502, detail=f"n8n error: {response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Media generation failed: {str(e)}")
