import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interview_agent.config import auth_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "users.json"


def _load_users() -> dict[str, dict]:
    if not _DB_PATH.is_file():
        return {}
    return json.loads(_DB_PATH.read_text(encoding="utf-8"))


def _save_users(users: dict[str, dict]) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DB_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def register(username: str, password: str, invite_code: str = "") -> str:
    users = _load_users()
    if username in users:
        logger.warning("register failed: username already exists user=%s", username)
        raise ValueError("Username already exists")
    valid_codes = auth_settings.get_invite_codes()
    if valid_codes and invite_code not in valid_codes:
        logger.warning("register failed: invalid invite code user=%s", username)
        raise ValueError("Invalid invite code")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    users[username] = {"password_hash": hashed}
    _save_users(users)
    logger.info("register success user=%s", username)
    return username


def authenticate(username: str, password: str) -> str:
    users = _load_users()
    stored = users.get(username, {}).get("password_hash", "")
    if not stored or not bcrypt.checkpw(password.encode(), stored.encode()):
        logger.warning("login failed user=%s", username)
        raise ValueError("Invalid credentials")
    logger.info("login success user=%s", username)
    return _create_token(username)


def _create_token(username: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=auth_settings.token_expire_hours)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, auth_settings.secret_key, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            auth_settings.secret_key,
            algorithms=["HS256"],
        )
        username = payload.get("sub")
        if username is None:
            logger.warning("token validation failed: missing sub claim")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        users = _load_users()
        if username not in users:
            logger.warning("token validation failed: user no longer exists user=%s", username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return username
    except jwt.ExpiredSignatureError:
        logger.warning("token validation failed: expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("token validation failed: invalid")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
