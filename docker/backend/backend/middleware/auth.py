"""
LUIN Authentication Middleware
Supabase JWT verification, tenant isolation, and session management.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional

from backend.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Decode and verify Supabase JWT token. Returns user payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
        )


def get_current_client_id(
    user_token: dict = Depends(get_current_user_token),
) -> str:
    """Extract client_id from JWT claims for tenant isolation."""
    client_id = user_token.get("app_metadata", {}).get("client_id")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No client workspace assigned. Contact support.",
        )
    return client_id


def require_admin(user_token: dict = Depends(get_current_user_token)) -> dict:
    """Verify admin role for dashboard access."""
    role = user_token.get("role", "anon")
    if role != "service_role" and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user_token
