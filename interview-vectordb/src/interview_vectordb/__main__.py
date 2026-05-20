import json
import sys
from pathlib import Path

import uvicorn

from interview_vectordb.api import api_app
from interview_vectordb.config import mcp_server_settings
from interview_vectordb.server import mcp

mcp_app = mcp.streamable_http_app()
api_app.mount("/mcp", mcp_app)


def _import_file(path: Path) -> None:
    from interview_vectordb.db import ProfileDB
    from interview_vectordb.schema import InterviewExperience

    data = json.loads(path.read_text(encoding="utf-8"))
    db = ProfileDB()
    if isinstance(data, list):
        exps = [InterviewExperience(**item) for item in data]
    else:
        exps = [InterviewExperience(**data)]
    ids = db.add_experiences(exps)
    print(f"Imported {len(ids)} experiences from {path.name}")


def import_experiences(path: str) -> None:
    p = Path(path)
    if p.is_file() and p.suffix == ".json":
        _import_file(p)
    elif p.is_dir():
        for f in sorted(p.glob("*.json")):
            _import_file(f)
    else:
        print(f"Path not found: {path}")


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "import" and len(sys.argv) > 2:
            import_experiences(sys.argv[2])
            return
        print("Usage: interview-vectordb import <path>")
        return
    uvicorn.run(api_app, host="0.0.0.0", port=mcp_server_settings.port)


if __name__ == "__main__":
    main()
