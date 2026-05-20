import json

from mcp.server.fastmcp import FastMCP

from interview_vectordb.config import mcp_server_settings
from interview_vectordb.db import ProfileDB

mcp = FastMCP("interview-vectordb", host="0.0.0.0", port=mcp_server_settings.port)

_db = ProfileDB()


@mcp.tool()
def get_profile(company: str, position: str) -> str:
    """Get interview profile for a company+position.
    Returns default profile if none exists.
    """
    profile = _db.get_or_generate_profile(company, position)
    return json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)


@mcp.tool()
def list_profiles() -> str:
    """List all available interview profiles."""
    profiles = _db.list_profiles()
    return json.dumps([p.model_dump() for p in profiles], ensure_ascii=False, indent=2)


@mcp.tool()
def delete_profile(company: str, position: str) -> str:
    """Delete a profile (e.g. after new experiences added)."""
    _db.delete_profile(company, position)
    return json.dumps({"deleted": f"{company}_{position}"})


@mcp.tool()
def batch_generate_profiles() -> str:
    """Regenerate all profiles from existing experiences."""
    results = _db.batch_generate_profiles()
    return json.dumps({k: v.model_dump() for k, v in results.items()}, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run(transport="streamable-http")
