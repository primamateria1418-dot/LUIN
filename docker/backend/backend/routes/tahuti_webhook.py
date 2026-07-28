"""
LUIN Tahuti CRM Webhook — Central CRM Integration
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import CampaignQueue, Client, CRMLog, CRMActionStatus, CRMChannel, CampaignStatus, get_db
from backend.models import CRMLogCreate, CRMLogResponse

logger = logging.getLogger("luin.crm")
router = APIRouter()
settings = get_settings()


class TahutiEvent(BaseModel):
    event_type: str = Field(..., description="Event type: client_profile, message_log, campaign_update, etc.")
    client_id: str = Field(..., description="Target client workspace ID")
    data: dict = Field(default_factory=dict, description="Event payload")
    channel: str = "hermes"
    signature: Optional[str] = None


class TahutiClientResponse(BaseModel):
    id: str
    name: str
    corporate_domain: Optional[str]
    status: str
    project_tag: str
    crm_logs_count: int = 0
    pending_campaigns: int = 0


@router.post("/crm/event")
async def tahuti_webhook(event: TahutiEvent, db: AsyncSession = Depends(get_db)):
    if event.event_type == "message_log":
        return await _handle_message_log(event, db)
    elif event.event_type == "campaign_update":
        return await _handle_campaign_update(event, db)
    elif event.event_type == "client_profile":
        return await _handle_client_profile(event, db)
    elif event.event_type == "bulk_crm":
        return await _handle_bulk_crm(event, db)
    raise HTTPException(status_code=400, detail=f"Unknown event type: {event.event_type}")


@router.post("/crm/log", status_code=201)
async def append_crm_log(log: CRMLogCreate, db: AsyncSession = Depends(get_db)):
    crm_entry = CRMLog(
        client_id=log.client_id, channel=CRMChannel(log.channel),
        message_text=log.message_text, action_item=log.action_item,
        status=CRMActionStatus(log.status), metadata_json=log.metadata_json,
    )
    db.add(crm_entry)
    await db.commit()
    await db.refresh(crm_entry)
    return CRMLogResponse(
        id=crm_entry.id, client_id=crm_entry.client_id, timestamp=crm_entry.timestamp,
        channel=crm_entry.channel.value, message_text=crm_entry.message_text,
        action_item=crm_entry.action_item, status=crm_entry.status.value,
    )


@router.get("/crm/client/{client_id}", response_model=TahutiClientResponse)
async def get_client_profile(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    logs_r = await db.execute(select(CRMLog).where(CRMLog.client_id == client.id))
    campaigns_r = await db.execute(select(CampaignQueue).where(CampaignQueue.client_id == client.id, CampaignQueue.status == CampaignStatus.PENDING))
    return TahutiClientResponse(
        id=str(client.id), name=client.name, corporate_domain=client.corporate_domain,
        status=client.status.value, project_tag=client.project_tag,
        crm_logs_count=len(logs_r.scalars().all()),
        pending_campaigns=len(campaigns_r.scalars().all()),
    )


@router.post("/crm/event/batch", status_code=200)
async def tahuti_bulk_webhook(events: list[TahutiEvent]):
    return {"processed": len(events), "events": [{"event_type": e.event_type, "status": "accepted"} for e in events]}


async def _handle_message_log(event: TahutiEvent, db: AsyncSession):
    log = CRMLog(client_id=event.client_id, channel=CRMChannel(event.channel), message_text=event.data.get("message", ""), action_item=event.data.get("action_item"), status=CRMActionStatus(event.data.get("status", "open")), metadata_json=event.data.get("metadata"))
    db.add(log)
    await db.commit()
    return {"status": "logged", "log_id": str(log.id)}


async def _handle_campaign_update(event: TahutiEvent, db: AsyncSession):
    campaign_id = event.data.get("campaign_id")
    new_status = event.data.get("status")
    feedback = event.data.get("feedback")
    result = await db.execute(select(CampaignQueue).where(CampaignQueue.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = CampaignStatus(new_status)
    if feedback:
        campaign.feedback_notes = feedback
    if new_status == "published":
        from datetime import datetime, timezone
        campaign.published_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "updated", "campaign_id": str(campaign.id), "new_status": new_status}


async def _handle_client_profile(event: TahutiEvent, db: AsyncSession):
    result = await db.execute(select(Client).where(Client.id == event.client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if "name" in event.data: client.name = event.data["name"]
    if "corporate_domain" in event.data: client.corporate_domain = event.data["corporate_domain"]
    if "status" in event.data: client.status = event.data["status"]
    await db.commit()
    return {"status": "updated", "client_id": str(client.id)}


async def _handle_bulk_crm(event: TahutiEvent, db: AsyncSession):
    actions = event.data.get("actions", [])
    results = []
    for action in actions:
        try:
            if action.get("type") == "log":
                db.add(CRMLog(client_id=event.client_id, message_text=action.get("message"), action_item=action.get("action_item")))
                results.append({"type": "log", "status": "ok"})
            elif action.get("type") == "campaign":
                db.add(CampaignQueue(client_id=event.client_id, platform=action.get("platform", "linkedin"), content_type=action.get("content_type", "text"), draft_text=action.get("draft_text")))
                results.append({"type": "campaign", "status": "ok"})
        except Exception as e:
            results.append({"type": action.get("type"), "status": "error", "error": str(e)})
    await db.commit()
    return {"status": "processed", "results": results}
