import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interview_agent.config import auth_settings

security = HTTPBearer()

_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "users.json"


def _load_users() -> dict[str, dict]:
    if not _DB_PATH.is_file():
        return {}
    return json.loads(_DB_PATH.read_text(encoding="utf-8"))


def _save_users(users: dict[str, dict]) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DB_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def register(username: str, password: str) -> str:
    users = _load_users()
    if username in users:
        raise ValueError("Username already exists")
    salt = uuid.uuid4().hex
    users[username] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return username


def authenticate(username: str, password: str) -> str:
    users = _load_users()
    user = users.get(username)
    if user is None or user["password_hash"] != _hash_password(password, user["salt"]):
        raise ValueError("Invalid credentials")
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        users = _load_users()
        if username not in users:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
