"""
LUIN Configuration Management
Loads settings from .env with production-safe defaults.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    APP_NAME: str = "LUIN Executive Marketing Engine"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # --- Supabase ---
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = "luin-dev-secret-change-in-production"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/luin"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # --- Groq ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""
    STRIPE_SUCCESS_URL: str = "https://luin.cc/billing/success"
    STRIPE_CANCEL_URL: str = "https://luin.cc/billing/cancel"

    # --- Tahuti / Hermes ---
    TAHUTI_GATEWAY_URL: str = "http://localhost:18789"
    TAHUTI_API_KEY: str = ""

    # --- Tavily ---
    TAVILY_API_KEY: str = ""

    # --- Apollo.io ---
    APOLLO_API_KEY: str = ""

    # --- ComfyUI ---
    COMFYUI_URL: str = "http://host.docker.internal:8188"

    # --- n8n ---
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/luin"

    # --- PostEverywhere ---
    POSTEVERYWHERE_API_KEY: str = ""

    # --- Security ---
    SECRET_KEY: str = "luin-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Allowed Corporate Domains (whitelist for generic email blocking) ---
    WHITELISTED_DOMAINS: str = "gmail.com,yahoo.com,hotmail.com"

    @property
    def whitelisted_domains_list(self) -> list[str]:
        return [d.strip() for d in self.WHITELISTED_DOMAINS.split(",") if d.strip()]

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,https://luin.cc"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
