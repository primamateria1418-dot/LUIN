"""
LUIN Pydantic Schemas — Input validation & API response models.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Enums for API ---
class CampaignPlatform(str, PyEnum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    BLOG = "blog"


class CampaignStatus(str, PyEnum):
    PENDING = "pending"
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr
    client_domain: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Client ---
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    corporate_domain: str = Field(..., min_length=1, max_length=255)
    email: EmailStr

    @field_validator("corporate_domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return v.strip().lower()


class ClientResponse(BaseModel):
    id: UUID
    name: str
    corporate_domain: Optional[str]
    status: str
    project_tag: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- CRM ---
class CRMLogCreate(BaseModel):
    client_id: UUID
    channel: str = "webhook"
    message_text: Optional[str] = None
    action_item: Optional[str] = None
    status: str = "open"
    metadata_json: Optional[dict] = None


class CRMLogResponse(BaseModel):
    id: UUID
    client_id: UUID
    timestamp: datetime
    channel: str
    message_text: Optional[str]
    action_item: Optional[str]
    status: str

    class Config:
        from_attributes = True


# --- Campaign ---
class CampaignCreate(BaseModel):
    client_id: UUID
    platform: str
    content_type: str = "text"
    draft_text: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: UUID
    client_id: UUID
    platform: str
    content_type: str
    draft_text: Optional[str]
    media_path: Optional[str]
    status: str
    scheduled_at: Optional[datetime]
    feedback_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignFeedback(BaseModel):
    campaign_id: UUID
    feedback_text: str = Field(..., min_length=1, max_length=5000)
    action: str = Field(..., pattern="^(approve|reject|edit)$")


# --- Brand Pack ---
class PaletteResponse(BaseModel):
    primary: str
    secondary: str
    accent: str
    neutral: str


class BrandPackResponse(BaseModel):
    palette: PaletteResponse
    svg_asset_path: Optional[str]
    logo_path: Optional[str]
    font_family: Optional[str]


# --- Groq Concierge ---
class ConciergeMessage(BaseModel):
    client_id: UUID
    message: str = Field(..., min_length=1, max_length=4000)
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None


class ConciergeResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    tool_result: Optional[dict] = None


# --- Billing ---
class CheckoutSessionRequest(BaseModel):
    client_id: UUID
    price_id: Optional[str] = None


class StripeWebhookEvent(BaseModel):
    event_type: str
    subscription_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
