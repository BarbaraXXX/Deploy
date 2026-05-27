from unittest.mock import MagicMock

import pytest

from interview_agent import session as session_module
from interview_agent.session import InterviewSession, SessionManager


@pytest.fixture
def mock_agent_build(monkeypatch):
    async def fake_build(*args, **kwargs):
        return MagicMock()

    monkeypatch.setattr("interview_agent.session.build_interview_agent", fake_build)


def _make_session() -> InterviewSession:
    return InterviewSession(agent=MagicMock(), domain="backend", difficulty="mid", username="u1")


def test_session_is_expired_false():
    s = _make_session()
    assert s.is_expired() is False


def test_session_is_expired_true(monkeypatch):
    s = _make_session()
    monkeypatch.setattr(session_module.time, "monotonic", lambda: s.created_at + session_module._SESSION_TTL_SECONDS + 1)
    assert s.is_expired() is True


def test_session_trim_messages():
    s = _make_session()
    s.messages = [MagicMock() for _ in range(session_module._MAX_MESSAGES_PER_SESSION + 50)]
    s.trim_messages()
    assert len(s.messages) == session_module._MAX_MESSAGES_PER_SESSION


def test_session_trim_messages_under_limit():
    s = _make_session()
    msgs = [MagicMock() for _ in range(10)]
    s.messages = list(msgs)
    s.trim_messages()
    assert s.messages == msgs


async def test_session_manager_create(mock_agent_build):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    assert isinstance(sid, str)
    assert sid in mgr._sessions


async def test_session_manager_get(mock_agent_build):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    got = mgr.get(sid, "alice")
    assert got is not None
    assert got.username == "alice"


async def test_session_manager_get_expired(mock_agent_build, monkeypatch):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    s = mgr._sessions[sid]
    monkeypatch.setattr(session_module.time, "monotonic", lambda: s.created_at + session_module._SESSION_TTL_SECONDS + 1)
    got = mgr.get(sid, "alice")
    assert got is None
    assert sid not in mgr._sessions


async def test_session_manager_get_wrong_user(mock_agent_build):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    assert mgr.get(sid, "bob") is None


async def test_session_manager_delete(mock_agent_build):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    mgr.delete(sid, "alice")
    assert mgr.get(sid, "alice") is None


async def test_session_manager_delete_wrong_user(mock_agent_build):
    mgr = SessionManager()
    sid = await mgr.create("backend", "mid", "alice")
    mgr.delete(sid, "bob")
    assert mgr.get(sid, "alice") is not None


async def test_session_manager_evict_expired(mock_agent_build, monkeypatch):
    mgr = SessionManager()
    sid1 = await mgr.create("backend", "mid", "alice")
    old = mgr._sessions[sid1]
    monkeypatch.setattr(session_module.time, "monotonic", lambda: old.created_at + session_module._SESSION_TTL_SECONDS + 1)
    sid2 = await mgr.create("backend", "mid", "bob")
    assert sid1 not in mgr._sessions
    assert sid2 in mgr._sessions


async def test_session_manager_max_sessions(mock_agent_build):
    mgr = SessionManager()
    created_ids = []
    for i in range(session_module._MAX_SESSIONS):
        sid = await mgr.create("backend", "mid", f"u{i}")
        created_ids.append(sid)
    new_sid = await mgr.create("backend", "mid", "newest")
    assert created_ids[0] not in mgr._sessions
    assert new_sid in mgr._sessions
    assert len(mgr._sessions) == session_module._MAX_SESSIONS
