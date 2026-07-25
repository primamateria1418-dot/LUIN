"""
LUIN Workspace API — Multi-tenant workspace management
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import Client, CampaignQueue, CRMLog, CampaignStatus, get_db

logger = logging.getLogger("luin.workspaces")
router = APIRouter()
settings = get_settings()


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    corporate_domain: Optional[str]
    status: str
    project_tag: str
    campaign_count: int = 0
    crm_log_count: int = 0


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]
    total: int


@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client))
    clients = result.scalars().all()
    workspaces = []
    for client in clients:
        campaign_r = await db.execute(select(CampaignQueue).where(CampaignQueue.client_id == client.id))
        crm_r = await db.execute(select(CRMLog).where(CRMLog.client_id == client.id))
        workspaces.append(WorkspaceResponse(
            id=str(client.id), name=client.name,
            corporate_domain=client.corporate_domain,
            status=client.status.value if hasattr(client.status, 'value') else str(client.status),
            project_tag=client.project_tag,
            campaign_count=len(campaign_r.scalars().all()),
            crm_log_count=len(crm_r.scalars().all()),
        ))
    return WorkspaceListResponse(workspaces=workspaces, total=len(workspaces))


@router.get("/workspaces/{workspace_id}/clients")
async def get_workspace_clients(workspace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == workspace_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found.")
    return {
        "id": str(client.id), "name": client.name,
        "corporate_domain": client.corporate_domain,
        "status": client.status.value if hasattr(client.status, 'value') else str(client.status),
        "project_tag": client.project_tag,
    }


@router.get("/workspaces/{workspace_id}/campaigns")
async def get_workspace_campaigns(workspace_id: str, limit: int = 50, offset: int = 0, platform: Optional[str] = None, status_filter: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(CampaignQueue).where(CampaignQueue.client_id == workspace_id)
    if platform: query = query.where(CampaignQueue.platform == platform)
    if status_filter: query = query.where(CampaignQueue.status == CampaignStatus(status_filter))
    query = query.order_by(CampaignQueue.scheduled_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    campaigns = result.scalars().all()
    return {
        "workspace_id": workspace_id,
        "campaigns": [{"id": str(c.id), "platform": c.platform, "content_type": c.content_type, "draft_text": c.draft_text, "status": c.status.value if hasattr(c.status, 'value') else str(c.status), "scheduled_at": str(c.scheduled_at) if c.scheduled_at else None, "created_at": str(c.created_at) if c.created_at else None} for c in campaigns],
        "total": len(campaigns),
    }


@router.get("/workspaces/{workspace_id}/crm-logs")
async def get_workspace_crm_logs(workspace_id: str, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    query = select(CRMLog).where(CRMLog.client_id == workspace_id).order_by(CRMLog.timestamp.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return {
        "workspace_id": workspace_id,
        "logs": [{"id": str(l.id), "channel": l.channel.value if hasattr(l.channel, 'value') else str(l.channel), "message_text": l.message_text, "action_item": l.action_item, "status": l.status.value if hasattr(l.status, 'value') else str(l.status), "timestamp": str(l.timestamp) if l.timestamp else None} for l in logs],
        "total": len(logs),
    }
