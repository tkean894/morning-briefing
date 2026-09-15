import base64
import functools
import logging

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

logger = logging.getLogger("uvicorn.error")


@functools.lru_cache
def _clerk_frontend_api_host() -> str:
    """Clerk publishable keys encode the instance's frontend API host, e.g.
    pk_test_<base64("sharp-camel-1570.clerk.accounts.dev$")>."""
    encoded = settings.clerk_publishable_key.split("_", 2)[-1]
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.b64decode(padded).decode("utf-8").rstrip("$")


@functools.lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    host = _clerk_frontend_api_host()
    return jwt.PyJWKClient(f"https://{host}/.well-known/jwks.json")


def _verify_session_token(token: str) -> str:
    """Verify a Clerk session JWT and return the Clerk user id (sub claim)."""
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(token, signing_key.key, algorithms=["RS256"])
    except jwt.PyJWTError as exc:
        logger.warning(
            "Clerk token verification failed: %s: %s", type(exc).__name__, exc
        )
        raise HTTPException(status_code=401, detail="Invalid session token") from exc
    return claims["sub"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1]
    clerk_user_id = _verify_session_token(token)

    user = db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    ).scalar_one_or_none()
    if user is None:
        user = User(clerk_user_id=clerk_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
