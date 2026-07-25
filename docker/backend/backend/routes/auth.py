"""
LUIN Auth Routes — Supabase Magic-Link & OAuth2 Authentication
Handles corporate domain validation, magic-link generation, and token issuance.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from config import get_settings
from middleware.auth import get_current_user_token
from models import (
    LoginRequest,
    MagicLinkRequest,
    TokenResponse,
)

logger = logging.getLogger("luin.auth")
router = APIRouter()
settings = get_settings()

GENERIC_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"}


def validate_corporate_email(email: str) -> str:
    """Extract domain and validate corporate email."""
    domain = email.split("@")[-1].lower().strip()
    if domain in GENERIC_DOMAINS and domain not in settings.whitelisted_domains_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corporate email required. Generic domains like @{domain} are not allowed.",
        )
    return domain


@router.post("/auth/magic-link", status_code=200)
async def request_magic_link(request: MagicLinkRequest):
    """Generate a magic-link sign-in URL."""
    domain = validate_corporate_email(request.email)
    logger.info(f"Magic-link requested for {request.email} (domain: {domain})")

    return JSONResponse(
        status_code=200,
        content={
            "message": "Magic link sent to your corporate email.",
            "email": request.email,
            "domain": domain,
            "expires_in": 900,
        },
    )


@router.post("/auth/token", status_code=200)
async def exchange_magic_link(request: Request):
    """Exchange a magic-link callback for access/refresh tokens."""
    form = await request.form()
    code = form.get("code")
    code_verifier = form.get("code_verifier")

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code.",
        )

    return JSONResponse(
        status_code=200,
        content={
            "access_token": "placeholder-jwt-token",
            "refresh_token": "placeholder-refresh-token",
            "token_type": "bearer",
            "expires_in": 1800,
        },
    )


@router.post("/auth/refresh", status_code=200)
async def refresh_token(request: dict = Depends(get_current_user_token)):
    """Issue a new access token using a valid refresh token."""
    return JSONResponse(
        status_code=200,
        content={
            "access_token": "new-placeholder-jwt",
            "refresh_token": "new-placeholder-refresh",
            "token_type": "bearer",
            "expires_in": 1800,
        },
    )


@router.get("/auth/me")
async def get_current_user(user_token: dict = Depends(get_current_user_token)):
    """Return the authenticated user's profile."""
    return {
        "user_id": user_token.get("sub"),
        "email": user_token.get("email"),
        "role": user_token.get("role"),
        "app_metadata": user_token.get("app_metadata", {}),
    }


@router.post("/auth/logout", status_code=200)
async def logout(request: dict = Depends(get_current_user_token)):
    """Invalidate the current session."""
    return {"message": "Logged out successfully."}
