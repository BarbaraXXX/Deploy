
from interview_agent import mcp_client


def test_build_server_config_empty(monkeypatch):
    monkeypatch.setattr(mcp_client.mcp_settings, "server_urls", "")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_command", "")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_args", "")
    assert mcp_client._build_server_config() == {}


def test_build_server_config_urls(monkeypatch):
    monkeypatch.setattr(
        mcp_client.mcp_settings,
        "server_urls",
        "http://localhost:9000/mcp, http://other:8000/other",
    )
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_command", "")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_args", "")
    cfg = mcp_client._build_server_config()
    assert len(cfg) == 2
    for entry in cfg.values():
        assert entry["transport"] == "http"
        assert entry["url"].startswith("http://")


def test_build_server_config_stdio(monkeypatch):
    monkeypatch.setattr(mcp_client.mcp_settings, "server_urls", "")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_command", "python")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_args", "-m my_server")
    cfg = mcp_client._build_server_config()
    assert "stdio_server" in cfg
    assert cfg["stdio_server"]["command"] == "python"
    assert cfg["stdio_server"]["args"] == ["-m", "my_server"]
    assert cfg["stdio_server"]["transport"] == "stdio"


async def test_get_mcp_tools_no_config(monkeypatch):
    monkeypatch.setattr(mcp_client.mcp_settings, "server_urls", "")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_command", "")
    tools = await mcp_client.get_mcp_tools()
    assert tools == []


async def test_get_mcp_tools_connection_failure(monkeypatch):
    monkeypatch.setattr(mcp_client.mcp_settings, "server_urls", "http://localhost:9999/mcp")
    monkeypatch.setattr(mcp_client.mcp_settings, "stdio_command", "")

    class BoomClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("connection failed")

    monkeypatch.setattr(mcp_client, "MultiServerMCPClient", BoomClient)
    tools = await mcp_client.get_mcp_tools()
    assert tools == []
