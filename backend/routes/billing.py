"""
LUIN Stripe Billing — Checkout Session & Webhook Integration
"""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import get_settings
from database import Client, get_db
from models import CheckoutSessionRequest

logger = logging.getLogger("luin.billing")
router = APIRouter()
settings = get_settings()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/billing/create-checkout-session", status_code=200)
async def create_checkout_session(request: CheckoutSessionRequest):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    price_id = request.price_id or settings.STRIPE_PRICE_ID
    if not price_id:
        raise HTTPException(status_code=400, detail="No price_id specified.")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            metadata={"client_id": str(request.client_id), "source": "luin_portal"},
            allow_promotion_codes=True,
        )
        return JSONResponse(content={"checkout_url": checkout_session.url, "session_id": checkout_session.id})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")


@router.post("/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=401, detail="Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        client_id = session.get("metadata", {}).get("client_id")
        subscription_id = session.get("subscription")
        if client_id and subscription_id:
            async with get_db() as db:
                result = await db.execute(Client.__selectable__.where(Client.id == client_id))
                client = result.scalar_one_or_none()
                if client:
                    client.stripe_subscription_id = subscription_id
                    client.stripe_customer_id = session.get("customer")
                    client.status = "active"
                    await db.commit()
                    logger.info(f"Workspace provisioned for client {client_id}")

    return JSONResponse(status_code=200, content={"received": True})
