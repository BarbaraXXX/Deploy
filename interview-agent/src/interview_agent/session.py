import uuid
from collections import OrderedDict

from langchain_core.messages import BaseMessage

from interview_agent.agent import build_interview_agent

_MAX_SESSIONS = 100
_MAX_MESSAGES_PER_SESSION = 200


class InterviewSession:
    def __init__(
        self, agent: object, domain: str, difficulty: str, username: str
    ) -> None:
        self.agent = agent
        self.domain = domain
        self.difficulty = difficulty
        self.username = username
        self.messages: list[BaseMessage] = []

    def trim_messages(self) -> None:
        if len(self.messages) > _MAX_MESSAGES_PER_SESSION:
            self.messages = self.messages[-_MAX_MESSAGES_PER_SESSION:]


class SessionManager:
    def __init__(self) -> None:
        self._sessions: OrderedDict[str, InterviewSession] = OrderedDict()

    async def create(
        self, domain: str, difficulty: str, username: str
    ) -> str:
        if len(self._sessions) >= _MAX_SESSIONS:
            self._sessions.popitem(last=False)

        agent = await build_interview_agent(domain, difficulty)
        session_id = uuid.uuid4().hex
        self._sessions[session_id] = InterviewSession(
            agent, domain, difficulty, username
        )
        return session_id

    def get(self, session_id: str, username: str | None = None) -> InterviewSession | None:
        session = self._sessions.get(session_id)
        if session is None:
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
