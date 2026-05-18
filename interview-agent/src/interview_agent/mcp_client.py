import logging

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from interview_agent.config import mcp_settings

logger = logging.getLogger(__name__)


def _build_server_config() -> dict:
    servers: dict = {}

    if mcp_settings.server_urls:
        for url in mcp_settings.server_urls.split(","):
            url = url.strip()
            if url:
                name = url.rstrip("/").split("/")[-1] or f"server_{len(servers)}"
                servers[name] = {"url": url, "transport": "http"}

    if mcp_settings.stdio_command:
        args = mcp_settings.stdio_args.split() if mcp_settings.stdio_args else []
        servers["stdio_server"] = {
            "command": mcp_settings.stdio_command,
            "args": args,
            "transport": "stdio",
        }

    return servers


async def get_mcp_tools() -> list[BaseTool]:
    server_config = _build_server_config()
    if not server_config:
        return []

    try:
        client = MultiServerMCPClient(server_config)
        tools = await client.get_tools()
        return tools
    except Exception:
        logger.warning("MCP servers unavailable, falling back to LLM-only mode", exc_info=True)
        return []
