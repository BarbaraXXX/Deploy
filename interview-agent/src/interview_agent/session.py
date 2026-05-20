import time
import uuid
from collections import OrderedDict

from langchain_core.messages import BaseMessage

from interview_agent.agent import build_interview_agent

_MAX_SESSIONS = 100
_MAX_MESSAGES_PER_SESSION = 200
_SESSION_TTL_SECONDS = 3600


class InterviewSession:
    def __init__(
        self, agent: object, domain: str, difficulty: str, username: str, structured_jd: str = ""
    ) -> None:
        self.agent = agent
        self.domain = domain
        self.difficulty = difficulty
        self.username = username
        self.structured_jd = structured_jd
        self.messages: list[BaseMessage] = []
        self.created_at: float = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > _SESSION_TTL_SECONDS

    def trim_messages(self) -> None:
        if len(self.messages) > _MAX_MESSAGES_PER_SESSION:
            self.messages = self.messages[-_MAX_MESSAGES_PER_SESSION:]


class SessionManager:
    def __init__(self) -> None:
        self._sessions: OrderedDict[str, InterviewSession] = OrderedDict()

    def _evict_expired(self) -> None:
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]

    async def create(
        self, domain: str, difficulty: str, username: str, structured_jd: str = ""
    ) -> str:
        self._evict_expired()
        if len(self._sessions) >= _MAX_SESSIONS:
            self._sessions.popitem(last=False)

        agent = await build_interview_agent(domain, difficulty, structured_jd)
        session_id = uuid.uuid4().hex
        self._sessions[session_id] = InterviewSession(
            agent, domain, difficulty, username, structured_jd
        )
        return session_id

    def get(self, session_id: str, username: str | None = None) -> InterviewSession | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            del self._sessions[session_id]
            return None
        if username is not None and session.username != username:
            return None
        return session

    def delete(self, session_id: str, username: str | None = None) -> None:
        session = self._sessions.get(session_id)
        if session is not None:
            if username is None or session.username == username:
                self._sessions.pop(session_id, None)


session_manager = SessionManager()
