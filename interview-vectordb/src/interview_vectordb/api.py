import json
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from interview_vectordb.db import ProfileDB, _EXPERIENCES_DIR
from interview_vectordb.schema import InterviewExperience

api_app = FastAPI(title="Interview VectorDB API")

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

_db = ProfileDB()

_MAX_IMPORT_BATCH = 500
_PATH_SEGMENT_RE = re.compile(r'^[\w\u4e00-\u9fff\s\-().&+,]+$')


def _validate_path_segment(value: str, name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail=f"{name} must not be empty")
    if ".." in stripped or len(stripped) > 128:
        raise HTTPException(status_code=400, detail=f"Invalid {name}")
    return stripped


@api_app.get("/api/profiles")
async def list_profiles() -> dict:
    profiles = _db.list_profiles()
    return {
        "profiles": [
            {
                "key": f"{p.company}_{p.position}",
                "company": p.company,
                "position": p.position,
                "difficulty_tendency": p.difficulty_tendency,
                "focus_areas": p.focus_areas,
                "key_traits": p.key_traits,
                "source_count": p.source_count,
            }
            for p in profiles
        ]
    }


@api_app.get("/api/profiles/{company}/{position}")
async def get_profile(company: str, position: str) -> dict:
    company = _validate_path_segment(company, "company")
    position = _validate_path_segment(position, "position")
    profile = _db.get_profile(company, position)
    if profile is None:
        profile = _db.get_or_generate_profile(company, position)
    return profile.model_dump()


@api_app.delete("/api/profiles/{company}/{position}")
async def delete_profile(company: str, position: str) -> dict:
    company = _validate_path_segment(company, "company")
    position = _validate_path_segment(position, "position")
    _db.delete_profile(company, position)
    return {"deleted": f"{company}_{position}"}


@api_app.post("/api/profiles/{company}/{position}/generate")
async def generate_profile(company: str, position: str) -> dict:
    company = _validate_path_segment(company, "company")
    position = _validate_path_segment(position, "position")
    profile = _db.generate_profile(company, position)
    if profile:
        _db.save_profile(profile)
        return profile.model_dump()
    return {"error": "No experiences found for this company/position"}


@api_app.get("/api/experiences/count")
async def experiences_count() -> dict:
    counts: dict[str, int] = {}
    for path in _EXPERIENCES_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            key = f"{data.get('company', '')}_{data.get('position', '')}"
            counts[key] = counts.get(key, 0) + 1
        except Exception:
            pass
    return {"counts": counts}


@api_app.post("/api/experiences/import")
async def import_experiences(experiences: list[InterviewExperience]) -> dict:
    if len(experiences) > _MAX_IMPORT_BATCH:
        raise HTTPException(status_code=400, detail=f"Max { _MAX_IMPORT_BATCH} experiences per request")
    ids = _db.add_experiences(experiences)
    return {"imported": len(ids), "ids": ids}
