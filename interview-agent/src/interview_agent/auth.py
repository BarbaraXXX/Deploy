import logging
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interview_agent.config import auth_settings
from interview_agent.db import create_user, get_user_by_username

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_USERNAME_MIN_LEN = 2
_USERNAME_MAX_LEN = 32
_PASSWORD_MIN_LEN = 6
_PASSWORD_MAX_LEN = 256


async def register(username: str, password: str, invite_code: str = "") -> None:
    username = username.strip()
    invite_code = invite_code.strip()
    if len(username) < _USERNAME_MIN_LEN or len(username) > _USERNAME_MAX_LEN:
        raise ValueError("Invalid username")
    if not username.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Invalid username")
    if len(password) < _PASSWORD_MIN_LEN or len(password) > _PASSWORD_MAX_LEN:
        raise ValueError("Invalid password")

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
    username = username.strip()
    if len(password) > _PASSWORD_MAX_LEN:
        raise ValueError("Invalid credentials")
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
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    token = request.cookies.get(auth_settings.cookie_name)
    if not token and credentials is not None:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token,
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
