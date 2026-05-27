import json
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from interview_agent import auth
from interview_agent.config import auth_settings


def _make_creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_register_success(isolate_env):
    auth.register("alice", "secret123")
    db_path = auth._DB_PATH
    assert db_path.is_file()
    data = json.loads(db_path.read_text(encoding="utf-8"))
    assert "alice" in data
    stored = data["alice"]["password_hash"]
    assert bcrypt.checkpw(b"secret123", stored.encode())
    assert stored != "secret123"


def test_register_duplicate(isolate_env):
    auth.register("bob", "password1")
    with pytest.raises(ValueError):
        auth.register("bob", "password2")


def test_authenticate_success(isolate_env):
    auth.register("carol", "mypassword")
    token = auth.authenticate("carol", "mypassword")
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_authenticate_wrong_password(isolate_env):
    auth.register("dave", "rightpass")
    with pytest.raises(ValueError):
        auth.authenticate("dave", "wrongpass")


def test_authenticate_nonexistent_user(isolate_env):
    with pytest.raises(ValueError):
        auth.authenticate("ghost", "whatever")


def test_create_token_has_exp_claim(isolate_env):
    token = auth._create_token("eve")
    payload = jwt.decode(token, auth_settings.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "eve"
    assert "exp" in payload


def test_get_current_user_valid_token(isolate_env):
    auth.register("frank", "passw0rd")
    token = auth._create_token("frank")
    username = auth.get_current_user(credentials=_make_creds(token))
    assert username == "frank"


def test_get_current_user_expired_token(isolate_env):
    auth.register("grace", "passw0rd")
    expired_payload = {
        "sub": "grace",
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    token = jwt.encode(expired_payload, auth_settings.secret_key, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=_make_creds(token))
    assert exc.value.status_code == 401


def test_get_current_user_invalid_token(isolate_env):
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=_make_creds("not.a.valid.token"))
    assert exc.value.status_code == 401


def test_get_current_user_deleted_user(isolate_env):
    auth.register("henry", "passw0rd")
    token = auth._create_token("henry")
    users = auth._load_users()
    del users["henry"]
    auth._save_users(users)
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=_make_creds(token))
    assert exc.value.status_code == 401


def test_load_users_empty(isolate_env):
    assert auth._load_users() == {}


def test_save_users_creates_dir(isolate_env, tmp_path, monkeypatch):
    nested = tmp_path / "deep" / "nest" / "users.json"
    monkeypatch.setattr(auth, "_DB_PATH", nested)
    auth._save_users({"x": {"password_hash": "h"}})
    assert nested.is_file()
    assert json.loads(nested.read_text(encoding="utf-8")) == {"x": {"password_hash": "h"}}
