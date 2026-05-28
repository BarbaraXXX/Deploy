import logging
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interview_agent.config import auth_settings
from interview_agent.db import create_user, get_user_by_username

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def register(username: str, password: str, invite_code: str = "") -> None:
    existing = await get_user_by_username(username)
    if existing is not None:
        logger.warning("register failed: username already exists user=%s", username)
        raise ValueError("Username already exists")

    valid_codes = auth_settings.get_invite_codes()
    if valid_codes and invite_code not in valid_codes:
        logger.warning("register failed: invalid invite code user=%s", username)
        raise ValueError("Invalid invite code")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    await create_user(username, hashed)
    logger.info("register success user=%s", username)


async def authenticate(username: str, password: str) -> str:
    user = await get_user_by_username(username)
    if user is None:
        logger.warning("login failed (no such user) user=%s", username)
        raise ValueError("Invalid credentials")

    stored = user["password_hash"]
    if not bcrypt.checkpw(password.encode(), stored.encode()):
        logger.warning("login failed (bad password) user=%s", username)
        raise ValueError("Invalid credentials")

    logger.info("login success user=%s", username)
    return _create_token(username)


def _create_token(username: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=auth_settings.token_expire_hours)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, auth_settings.secret_key, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            auth_settings.secret_key,
            algorithms=["HS256"],
        )
        username: str | None = payload.get("sub")
        if username is None:
            logger.warning("token validation failed: missing sub claim")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        user = await get_user_by_username(username)
        if user is None:
            logger.warning("token validation failed: user no longer exists user=%s", username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return username
    except jwt.ExpiredSignatureError:
        logger.warning("token validation failed: expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("token validation failed: invalid")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
