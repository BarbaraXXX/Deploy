
import pytest
from fastapi.testclient import TestClient

from interview_agent import server as server_module
from interview_agent.auth import get_current_user
from interview_agent.jd_parser import StructuredJD


@pytest.fixture
def client(isolate_env):
    return TestClient(server_module.app)


@pytest.fixture
def auth_client(client):
    server_module.app.dependency_overrides[get_current_user] = lambda: "tester"
    yield client
    server_module.app.dependency_overrides.pop(get_current_user, None)


def test_register_success(client):
    resp = client.post("/api/auth/register", json={"username": "alice", "password": "secret1"})
    assert resp.status_code == 200
    body = resp.json()
    assert "token" in body
    assert body["username"] == "alice"


def test_register_short_username(client):
    resp = client.post("/api/auth/register", json={"username": "a", "password": "secret1"})
    assert resp.status_code == 400


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={"username": "alice", "password": "12"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register", json={"username": "bob", "password": "secret1"})
    resp = client.post("/api/auth/login", json={"username": "bob", "password": "secret1"})
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1"})
    resp = client.post("/api/auth/login", json={"username": "carol", "password": "wrong"})
    assert resp.status_code == 401


def test_me_authenticated(auth_client):
    resp = auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"username": "tester"}


def test_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


def test_list_domains(client):
    resp = client.get("/api/domains")
    assert resp.status_code == 200
    body = resp.json()
    assert "presets" in body
    assert "backend" in body["presets"]
    assert len(body["presets"]) == 8


def test_sanitize_path_segment_normal():
    assert server_module._sanitize_path_segment("hello-world") == "hello-world"


def test_sanitize_path_segment_traversal():
    assert server_module._sanitize_path_segment("..") == ""
    assert server_module._sanitize_path_segment("foo/../bar") == ""


def test_sanitize_path_segment_slash():
    assert server_module._sanitize_path_segment("/") == ""
    assert server_module._sanitize_path_segment("a/b") == ""
    assert server_module._sanitize_path_segment("a\\b") == ""


def test_sanitize_path_segment_length():
    out = server_module._sanitize_path_segment("x" * 500)
    assert len(out) == 128


def test_format_jd_full():
    jd = StructuredJD(
        position_title="Backend Engineer",
        required_skills=["Python", "PostgreSQL"],
        required_experience="3+ years",
        key_responsibilities=["Build APIs"],
        preferred_qualifications=["AWS"],
        tech_stack=["FastAPI"],
        interview_focus="system design",
    )
    out = server_module._format_jd(jd)
    assert "Backend Engineer" in out
    assert "Python" in out
    assert "PostgreSQL" in out
    assert "3+ years" in out
    assert "Build APIs" in out
    assert "AWS" in out
    assert "FastAPI" in out
    assert "system design" in out


def test_format_jd_empty():
    jd = StructuredJD()
    assert server_module._format_jd(jd) == ""


def test_format_profile_full():
    data = {
        "company": "Acme",
        "position": "SWE",
        "difficulty_tendency": "senior",
        "focus_areas": ["distributed systems"],
        "interview_style": "deep technical",
        "question_types": ["system design"],
        "key_traits": ["pragmatic"],
        "source_count": 5,
    }
    out = server_module._format_profile(data)
    assert "Acme" in out
    assert "SWE" in out
    assert "高级" in out
    assert "distributed systems" in out
    assert "deep technical" in out
    assert "system design" in out
    assert "pragmatic" in out
    assert "5" in out


def test_format_profile_empty():
    assert server_module._format_profile({}) == ""
