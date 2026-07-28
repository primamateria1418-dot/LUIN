"""
LUIN Groq AI Concierge — Real-time Streaming Chat Interface
Powered by Groq API with function calling for client actions.
"""

import json
import logging
from typing import AsyncGenerator, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from backend.config import get_settings
from backend.middleware.auth import get_current_user_token
from backend.models import ConciergeMessage, ConciergeResponse

logger = logging.getLogger("luin.assistant")
router = APIRouter()
settings = get_settings()

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_brand_focus",
            "description": "Update the client's marketing focus keywords and campaign emphasis topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "The client's workspace ID"},
                    "focus_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keywords/topics to emphasize",
                    },
                },
                "required": ["client_id", "focus_topics"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_adhoc_post",
            "description": "Queue an immediate post draft for agency review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                    "platform": {
                        "type": "string",
                        "enum": ["twitter", "linkedin", "facebook", "instagram", "tiktok"],
                    },
                    "topic": {"type": "string", "description": "The post topic/content"},
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Priority level",
                    },
                },
                "required": ["client_id", "platform", "topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_feedback",
            "description": "Send client feedback to Tahuti admin dashboard via webhook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                    "campaign_id": {"type": "string", "description": "Campaign being reviewed"},
                    "feedback_text": {
                        "type": "string",
                        "description": "Client's feedback or revision request",
                    },
                },
                "required": ["client_id", "campaign_id", "feedback_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_campaign_status",
            "description": "Fetch live engagement metrics and upcoming post schedules for a client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                },
                "required": ["client_id"],
            },
        },
    },
]

CONCIERGE_SYSTEM_PROMPT = """You are the LUIN Executive Concierge — a sharp, professional AI assistant
for high-tier marketing automation. You help clients manage their campaigns, review content,
and optimize their marketing strategy.

Tone: Professional, direct, data-driven. No fluff. No AI-isms like "delve," "elevated," "tapestry,"
"realm," "supercharge," or "game-changer."

When using tools, call them with the correct parameters. Never fabricate campaign data.
If you don't have enough information to call a tool, ask the client for the missing details."""


async def call_groq_stream(messages: list, client_id: str) -> AsyncGenerator[str, None]:
    """Stream responses from Groq API via SSE."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "tools": GROQ_TOOLS,
            "stream": True,
            "temperature": 0.3,
            "max_tokens": 2048,
        }

        async with client.stream(
            "POST",
            f"{settings.GROQ_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                yield f"data: {json.dumps({'error': f'Groq API error: {response.status_code}', 'detail': error_body.decode()})}\n\n"
                return

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                try:
                    data = json.loads(data_str)
                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    if "content" in delta and delta["content"]:
                        yield f"data: {json.dumps({'type': 'content', 'text': delta['content']})}\n\n"

                    if delta.get("tool_calls"):
                        for tool_call in delta["tool_calls"]:
                            yield f"data: {json.dumps({'type': 'tool_call', 'tool_call': tool_call})}\n\n"

                except json.JSONDecodeError:
                    continue


@router.post("/assistant/groq", response_class=StreamingResponse)
async def groq_concierge_stream(request: ConciergeMessage):
    """POST /api/v1/assistant/groq — Real-time streaming AI concierge."""
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq API key not configured.",
        )

    system_msg = {"role": "system", "content": CONCIERGE_SYSTEM_PROMPT}

    if request.tool_name:
        tool_msg = {
            "role": "tool",
            "tool_call_id": "luin_tool_1",
            "content": json.dumps(request.tool_args or {}),
        }
        messages = [system_msg, tool_msg]
    else:
        user_msg = {
            "role": "user",
            "content": f"[client_id: {request.client_id}] {request.message}",
        }
        messages = [system_msg, user_msg]

    return StreamingResponse(
        call_groq_stream(messages, request.client_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/assistant/groq/sync", status_code=200)
async def groq_concierge_sync(request: ConciergeMessage):
    """POST /api/v1/assistant/groq/sync — Non-streaming version for tool calls."""
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq API key not configured.",
        )

    tool_name = request.tool_name
    tool_args = request.tool_args or {}

    logger.info(f"Executing tool: {tool_name} for client {request.client_id}")

    return ConciergeResponse(
        reply=f"Tool `{tool_name}` executed for client {request.client_id}.",
        tool_used=tool_name,
        tool_result=tool_args,
    )
