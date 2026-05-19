import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from interview_agent.auth import authenticate, get_current_user, register
from interview_agent.config import llm_settings
from interview_agent.prompts import PRESET_DOMAINS
from interview_agent.session import session_manager

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "web" / "dist"

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app = FastAPI(title="Interview Agent")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

_MAX_MESSAGE_LEN = 4000


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def api_register(request: Request, req: RegisterRequest) -> dict:
    if len(req.username) < 2 or len(req.username) > 32:
        raise HTTPException(status_code=400, detail="Username must be 2-32 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    try:
        register(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = authenticate(req.username, req.password)
    return {"token": token, "username": req.username}


@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def api_login(request: Request, req: LoginRequest) -> dict:
    try:
        token = authenticate(req.username, req.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token, "username": req.username}


@app.get("/api/auth/me")
async def api_me(username: str = Depends(get_current_user)) -> dict:
    return {"username": username}


class CreateSessionRequest(BaseModel):
    domain: str
    difficulty: str = "mid"


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/api/domains")
async def list_domains() -> dict:
    return {"presets": list(PRESET_DOMAINS.keys())}


@app.get("/api/providers")
async def list_providers(username: str = Depends(get_current_user)) -> dict:
    providers = llm_settings.get_providers()
    return {
        "default": llm_settings.default_provider,
        "available": list(providers.keys()),
    }


@app.post("/api/sessions")
async def create_session(
    req: CreateSessionRequest, username: str = Depends(get_current_user)
) -> dict:
    if len(req.domain) > 64:
        raise HTTPException(status_code=400, detail="Domain name too long")
    session_id = await session_manager.create(req.domain, req.difficulty, username)
    return {"session_id": session_id}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, username: str = Depends(get_current_user)):
    if len(req.message) > _MAX_MESSAGE_LEN:
        raise HTTPException(status_code=400, detail="Message too long")

    session = session_manager.get(req.session_id, username)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    human_msg = HumanMessage(content=req.message)
    session.messages.append(human_msg)

    async def event_generator():
        full_content = ""
        async for event in session.agent.astream_events(
            {"messages": session.messages},
            version="v2",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    text = chunk.content if isinstance(chunk.content, str) else ""
                    if text:
                        full_content += text
                        yield f"data: {json.dumps({'type': 'token', 'content': text}, ensure_ascii=False)}\n\n"
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name}, ensure_ascii=False)}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end'}, ensure_ascii=False)}\n\n"

        session.messages.append(AIMessage(content=full_content))
        session.trim_messages()
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str, username: str = Depends(get_current_user)
) -> dict:
    session_manager.delete(session_id, username)
    return {"ok": True}


if _STATIC_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = (_STATIC_DIR / full_path).resolve()
        if not str(file_path).startswith(str(_STATIC_DIR.resolve())):
            raise HTTPException(status_code=404)
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_STATIC_DIR / "index.html")


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
