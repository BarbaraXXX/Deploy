import asyncio
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from interview_agent.agent import build_interview_agent

from .candidate import build_candidate_llm, generate_candidate_response, get_candidate_system_prompt
from .config import test_settings
from .evaluator import evaluate_session
from .recorder import SessionRecorder
from .schemas import QAPair, TestConfig, TestSession

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "web"

app = FastAPI(title="Interview Tester")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

_END_KEYWORDS = ("面试结束", "感谢参与", "本次面试", "总结", "overall")


def _is_interview_ending(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _END_KEYWORDS)


class StartTestRequest(BaseModel):
    domain: str = "backend"
    difficulty: str = "mid"
    candidate_level: str = "mid"
    max_rounds: int = 50


@app.post("/api/test/stream")
async def stream_test(req: StartTestRequest):
    config = TestConfig(
        domain=req.domain,
        difficulty=req.difficulty,
        candidate_level=req.candidate_level,
        max_rounds=req.max_rounds,
    )

    async def event_generator():
        now = datetime.now(timezone.utc)
        session_id = f"test_{now.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

        session = TestSession(
            session_id=session_id,
            config=config,
            started_at=now.isoformat(),
        )
        recorder = SessionRecorder(session, test_settings.data_dir)
        recorder.save()

        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'config': config.model_dump()}, ensure_ascii=False)}\n\n"

        try:
            agent = await build_interview_agent(config.domain, config.difficulty)
            candidate_llm = build_candidate_llm(config.candidate_level)
            candidate_prompt = get_candidate_system_prompt(config.domain, config.candidate_level)

            interview_messages: list = [HumanMessage(content="你好，我准备好面试了。")]
            candidate_messages: list = []

            result = await agent.ainvoke({"messages": interview_messages})
            interview_messages = result["messages"]

            for round_num in range(1, config.max_rounds + 1):
                interviewer_msg = interview_messages[-1]
                if not isinstance(interviewer_msg, AIMessage):
                    break

                question_text = interviewer_msg.content
                question_ts = datetime.now(timezone.utc).isoformat()

                yield f"data: {json.dumps({'type': 'question', 'round': round_num, 'content': question_text, 'timestamp': question_ts}, ensure_ascii=False)}\n\n"

                candidate_messages.append(HumanMessage(content=question_text))
                answer_text = await generate_candidate_response(
                    candidate_messages, candidate_llm, candidate_prompt
                )
                answer_ts = datetime.now(timezone.utc).isoformat()
                candidate_messages.append(AIMessage(content=answer_text))

                qa = QAPair(
                    round=round_num,
                    question=question_text,
                    answer=answer_text,
                    question_timestamp=question_ts,
                    answer_timestamp=answer_ts,
                )
                recorder.record_qa(qa)
                recorder.save()

                yield f"data: {json.dumps({'type': 'answer', 'round': round_num, 'content': answer_text, 'timestamp': answer_ts}, ensure_ascii=False)}\n\n"

                if _is_interview_ending(question_text):
                    yield f"data: {json.dumps({'type': 'ending', 'reason': 'interview_ended'}, ensure_ascii=False)}\n\n"
                    break

                interview_messages.append(HumanMessage(content=answer_text))
                result = await agent.ainvoke({"messages": interview_messages})
                interview_messages = result["messages"]

            recorder.mark_completed()

            yield f"data: {json.dumps({'type': 'evaluating'}, ensure_ascii=False)}\n\n"

            evaluation = await evaluate_session(session)
            session.evaluation = evaluation
            recorder.save()

            yield f"data: {json.dumps({'type': 'evaluation', 'data': evaluation.model_dump()}, ensure_ascii=False)}\n\n"

        except Exception as e:
            recorder.mark_error(str(e))
            recorder.save()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/sessions")
async def list_sessions():
    data_dir = test_settings.data_dir
    if not data_dir.is_dir():
        return {"sessions": []}
    sessions = []
    for f in sorted(data_dir.glob("test_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id", f.stem),
                "domain": data.get("config", {}).get("domain", ""),
                "difficulty": data.get("config", {}).get("difficulty", ""),
                "total_rounds": data.get("total_rounds", 0),
                "status": data.get("status", ""),
                "started_at": data.get("started_at", ""),
                "overall_score": (data.get("evaluation") or {}).get("overall_score", None),
            })
        except Exception:
            pass
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    safe_id = session_id.replace("..", "").replace("/", "").replace("\\", "")
    path = test_settings.data_dir / f"{safe_id}.json"
    if not path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


_INDEX_HTML = _STATIC_DIR / "index.html"


if _INDEX_HTML.is_file():
    @app.get("/")
    async def serve_index():
        return FileResponse(
            _INDEX_HTML,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )


def run() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
