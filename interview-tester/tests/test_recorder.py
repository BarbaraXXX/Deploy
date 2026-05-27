import json

from interview_tester.recorder import SessionRecorder
from interview_tester.schemas import Evaluation, QAPair, TestConfig, TestSession


def _new_session() -> TestSession:
    return TestSession(
        session_id="sid_test",
        config=TestConfig(),
        started_at="2024-01-01T00:00:00+00:00",
    )


def test_record_qa(tmp_path):
    session = _new_session()
    recorder = SessionRecorder(session, tmp_path)
    qa = QAPair(
        round=1,
        question="q",
        answer="a",
        question_timestamp="t1",
        answer_timestamp="t2",
    )
    recorder.record_qa(qa)
    assert len(session.qa_pairs) == 1
    assert session.qa_pairs[0] is qa
    assert session.total_rounds == 1


def test_save_creates_file(tmp_path):
    session = _new_session()
    recorder = SessionRecorder(session, tmp_path)
    path = recorder.save()
    assert path.exists()
    assert path.name == "sid_test.json"


def test_save_content_valid(tmp_path):
    session = _new_session()
    recorder = SessionRecorder(session, tmp_path)
    recorder.record_qa(QAPair(
        round=1,
        question="q1",
        answer="a1",
        question_timestamp="ts1",
        answer_timestamp="ts2",
    ))
    path = recorder.save()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["session_id"] == "sid_test"
    assert data["total_rounds"] == 1
    assert data["qa_pairs"][0]["question"] == "q1"
    assert data["qa_pairs"][0]["answer"] == "a1"
    assert data["status"] == "running"


def test_mark_completed(tmp_path):
    session = _new_session()
    recorder = SessionRecorder(session, tmp_path)
    recorder.mark_completed()
    assert session.status == "completed"
    assert session.ended_at != ""


def test_mark_error_no_evaluation(tmp_path):
    session = _new_session()
    recorder = SessionRecorder(session, tmp_path)
    recorder.mark_error("boom")
    assert session.status == "error"
    assert session.ended_at != ""
    assert session.evaluation is not None
    assert session.evaluation.summary == "[ERROR] boom"
    assert session.evaluation.overall_score == 0


def test_mark_error_with_evaluation(tmp_path):
    session = _new_session()
    session.evaluation = Evaluation(
        style_naturalness=5,
        difficulty_appropriateness=5,
        follow_up_quality=5,
        topic_coverage=5,
        overall_score=5,
        strengths=[],
        weaknesses=[],
        summary="existing",
        improvement_suggestions=[],
    )
    recorder = SessionRecorder(session, tmp_path)
    recorder.mark_error("boom")
    assert session.status == "error"
    assert "existing" in session.evaluation.summary
    assert "[ERROR] boom" in session.evaluation.summary
