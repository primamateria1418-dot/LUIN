"""
LUIN Campaign Management Routes
Handles content scheduling, approval workflows, and social media dispatch.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import CampaignQueue, Client, CampaignStatus, get_db
from models import CampaignCreate, CampaignFeedback, CampaignResponse

logger = logging.getLogger("luin.campaigns")
router = APIRouter()
settings = get_settings()


class CampaignListFilter(BaseModel):
    client_id: str
    platform: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    client_id: str,
    platform: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List campaigns for a client with optional filters."""
    query = select(CampaignQueue).where(CampaignQueue.client_id == client_id)

    if platform:
        query = query.where(CampaignQueue.platform == platform)
    if status_filter:
        query = query.where(CampaignQueue.status == CampaignStatus(status_filter))

    query = query.order_by(CampaignQueue.scheduled_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    campaigns = result.scalars().all()

    return [
        CampaignResponse(
            id=c.id,
            client_id=c.client_id,
            platform=c.platform,
            content_type=c.content_type,
            draft_text=c.draft_text,
            media_path=c.media_path,
            status=c.status.value,
            scheduled_at=c.scheduled_at,
            feedback_notes=c.feedback_notes,
            created_at=c.created_at,
        )
        for c in campaigns
    ]


@router.post("/campaigns", status_code=201)
async def create_campaign(
    campaign: CampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new campaign entry in the queue."""
    new_campaign = CampaignQueue(
        client_id=campaign.client_id,
        platform=campaign.platform,
        content_type=campaign.content_type,
        draft_text=campaign.draft_text,
        scheduled_at=campaign.scheduled_at,
        status=CampaignStatus.PENDING,
    )
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)

    return CampaignResponse(
        id=new_campaign.id,
        client_id=new_campaign.client_id,
        platform=new_campaign.platform,
        content_type=new_campaign.content_type,
        draft_text=new_campaign.draft_text,
        media_path=new_campaign.media_path,
        status=new_campaign.status.value,
        scheduled_at=new_campaign.scheduled_at,
        feedback_notes=new_campaign.feedback_notes,
        created_at=new_campaign.created_at,
    )


@router.post("/campaigns/{campaign_id}/feedback")
async def submit_feedback(
    campaign_id: str,
    feedback: CampaignFeedback,
    db: AsyncSession = Depends(get_db),
):
    """Approve, edit, or reject a campaign with feedback notes."""
    result = await db.execute(
        select(CampaignQueue).where(CampaignQueue.id == feedback.campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if feedback.action == "approve":
        campaign.status = CampaignStatus.APPROVED
    elif feedback.action == "reject":
        campaign.status = CampaignStatus.REJECTED
    elif feedback.action == "edit":
        campaign.status = CampaignStatus.DRAFT

    campaign.feedback_notes = feedback.feedback_text
    await db.commit()

    return {"status": "feedback recorded", "campaign_id": str(campaign.id), "action": feedback.action}


@router.put("/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status_val: str,
    db: AsyncSession = Depends(get_db),
):
    """Update a campaign's status (admin operation)."""
    result = await db.execute(
        select(CampaignQueue).where(CampaignQueue.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus(status_val)
    if status_val == "published":
        from datetime import datetime, timezone
        campaign.published_at = datetime.now(timezone.utc)

    await db.commit()
    return {"status": "updated", "campaign_id": campaign_id, "new_status": status_val}


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single campaign by ID."""
    result = await db.execute(
        select(CampaignQueue).where(CampaignQueue.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignResponse(
        id=campaign.id,
        client_id=campaign.client_id,
        platform=campaign.platform,
        content_type=campaign.content_type,
        draft_text=campaign.draft_text,
        media_path=campaign.media_path,
        status=campaign.status.value,
        scheduled_at=campaign.scheduled_at,
        feedback_notes=campaign.feedback_notes,
        created_at=campaign.created_at,
    )


@router.get("/campaigns/stats/{client_id}")
async def get_campaign_stats(
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get campaign statistics for a client."""
    result = await db.execute(
        select(CampaignQueue).where(CampaignQueue.client_id == client_id)
    )
    all_campaigns = result.scalars().all()

    stats = {
        "total": len(all_campaigns),
        "by_status": {},
        "by_platform": {},
    }

    for c in all_campaigns:
        status_key = c.status.value
        stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
        stats["by_platform"][c.platform] = stats["by_platform"].get(c.platform, 0) + 1

    return stats
