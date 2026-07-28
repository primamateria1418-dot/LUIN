"""
LUIN Database Models & Async SQLAlchemy Setup
Multi-tenant schema with Supabase-compatible PostgreSQL design.
"""

from datetime import datetime, timezone
from typing import Optional

from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    DateTime,
    Enum as sa_enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from backend.config import get_settings

settings = get_settings()

# --- Engine Setup ---
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


# --- Enums (Python standard library) ---
class ClientStatus(PyEnum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CHURNED = "churned"


class CampaignStatus(PyEnum):
    PENDING = "pending"
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class CRMChannel(PyEnum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    HERMES = "hermes"


class CRMActionStatus(PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ESCALATED = "escalated"


# --- Models ---
class Client(Base):
    """Multi-tenant client workspace."""
    __tablename__ = "clients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    corporate_domain = Column(String(255), nullable=True)
    status = Column(sa_enum(ClientStatus), default=ClientStatus.TRIAL)
    stripe_subscription_id = Column(String(512), nullable=True)
    stripe_customer_id = Column(String(512), nullable=True)
    project_tag = Column(String(64), default="#luin")
    # Dynamic Client Control fields
    posting_schedule = Column(JSONB, nullable=True)  # [{day, time, platform}]
    brand_voice = Column(Text, nullable=True)  # Updated brand voice/tone
    content_frequency = Column(String(64), nullable=True)  # daily, weekly, bi-weekly, monthly
    key_messages = Column(JSONB, nullable=True)  # [key brand messages]
    target_audience = Column(JSONB, nullable=True)  # {age_range, interests, location}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    crm_logs = relationship("CRMLog", back_populates="client", cascade="all, delete-orphan")
    campaign_queue = relationship("CampaignQueue", back_populates="client", cascade="all, delete-orphan")
    brand_tokens = relationship("BrandToken", back_populates="client", cascade="all, delete-orphan")


class CRMLog(Base):
    """Tahuti/Hermes CRM message log."""
    __tablename__ = "crm_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    channel = Column(sa_enum(CRMChannel), default=CRMChannel.WEBHOOK)
    message_text = Column(Text, nullable=True)
    action_item = Column(Text, nullable=True)
    status = Column(sa_enum(CRMActionStatus), default=CRMActionStatus.OPEN)
    metadata_json = Column(JSONB, nullable=True)

    client = relationship("Client", back_populates="crm_logs")


class CampaignQueue(Base):
    """Content scheduling queue."""
    __tablename__ = "campaign_queue"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(64), nullable=False)  # twitter, linkedin, facebook, instagram, tiktok, blog
    content_type = Column(String(64), default="text")  # text, image, video, blog
    draft_text = Column(Text, nullable=True)
    media_path = Column(String(512), nullable=True)
    status = Column(sa_enum(CampaignStatus), default=CampaignStatus.PENDING)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="campaign_queue")


class BrandToken(Base):
    """Client brand palette & asset tokens."""
    __tablename__ = "brand_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    client_id = Column(PG_UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    primary_color = Column(String(7), nullable=True)  # hex
    secondary_color = Column(String(7), nullable=True)
    accent_color = Column(String(7), nullable=True)
    font_family = Column(String(128), nullable=True)
    svg_asset_path = Column(String(512), nullable=True)
    logo_png_path = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="brand_tokens")


# --- Session Helpers ---
async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def seed_initial_clients(session: AsyncSession):
    """Pre-seed three active workspaces on launch."""
    from sqlalchemy import select

    result = await session.execute(select(func.count()).select_from(Client))
    count = result.scalar_one()
    if count > 0:
        return  # Already seeded

    clients_data = [
        Client(
            id=PG_UUID(hex="a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            name="1095 Apparel",
            corporate_domain="1095apparel.com",
            status=ClientStatus.ACTIVE,
            project_tag="#shopify",
        ),
        Client(
            id=PG_UUID(hex="b2c3d4e5-f6a7-8901-bcde-f12345678901"),
            name="United Planet",
            corporate_domain="unitedplanet.org",
            status=ClientStatus.ACTIVE,
            project_tag="#luin",
        ),
        Client(
            id=PG_UUID(hex="c3d4e5f6-a7b8-9012-cdef-123456789012"),
            name="LUIN Agency",
            corporate_domain="luin.cc",
            status=ClientStatus.ACTIVE,
            project_tag="#luin",
        ),
    ]
    for client in clients_data:
        session.add(client)
    await session.commit()
