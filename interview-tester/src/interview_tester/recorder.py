import json
from datetime import datetime, timezone
from pathlib import Path

from .schemas import QAPair, TestSession


class SessionRecorder:
    def __init__(self, session: TestSession, data_dir: Path) -> None:
        self.session = session
        self.data_dir = data_dir

    def record_qa(self, qa: QAPair) -> None:
        self.session.qa_pairs.append(qa)
        self.session.total_rounds = len(self.session.qa_pairs)

    def save(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / f"{self.session.session_id}.json"
        data = self.session.model_dump(exclude_none=False)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def mark_completed(self) -> None:
        self.session.status = "completed"
        self.session.ended_at = datetime.now(timezone.utc).isoformat()

    def mark_error(self, error_msg: str) -> None:
        self.session.status = "error"
        self.session.ended_at = datetime.now(timezone.utc).isoformat()
        self.session.evaluation = self.session.evaluation or None
        existing_summary = ""
        if self.session.evaluation and self.session.evaluation.summary:
            existing_summary = self.session.evaluation.summary + "\n"
        if not self.session.evaluation:
            from .schemas import Evaluation
            self.session.evaluation = Evaluation(
                style_naturalness=0,
                difficulty_appropriateness=0,
                follow_up_quality=0,
                topic_coverage=0,
                overall_score=0,
                strengths=[],
                weaknesses=[],
                summary=f"[ERROR] {error_msg}",
                improvement_suggestions=[],
            )
        else:
            self.session.evaluation.summary = f"{existing_summary}[ERROR] {error_msg}"
