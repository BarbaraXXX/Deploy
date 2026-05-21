import argparse
import asyncio
import random
from datetime import datetime, timezone

from langchain_core.messages import AIMessage, HumanMessage

from interview_agent.agent import build_interview_agent

from .candidate import build_candidate_llm, generate_candidate_response, get_candidate_system_prompt
from .config import test_settings
from .evaluator import evaluate_session
from .recorder import SessionRecorder
from .schemas import QAPair, TestConfig, TestSession


_END_KEYWORDS = ("面试结束", "感谢参与", "本次面试", "总结", "overall")


def _is_interview_ending(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _END_KEYWORDS)


async def run_test(config: TestConfig) -> TestSession:
    now = datetime.now(timezone.utc)
    session_id = f"test_{now.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

    session = TestSession(
        session_id=session_id,
        config=config,
        started_at=now.isoformat(),
    )

    recorder = SessionRecorder(session, test_settings.data_dir)
    recorder.save()

    print(f"[{session_id}] 开始面试测试...")
    print(f"  领域: {config.domain} | 难度: {config.difficulty} | 候选人水平: {config.candidate_level}")

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

        print(f"  第{round_num}轮完成")

        if _is_interview_ending(question_text):
            print("  检测到面试结束信号")
            break

        interview_messages.append(HumanMessage(content=answer_text))
        result = await agent.ainvoke({"messages": interview_messages})
        interview_messages = result["messages"]

    recorder.mark_completed()

    print("  正在评估面试表现...")
    evaluation = await evaluate_session(session)
    session.evaluation = evaluation

    recorder.save()

    print(f"\n=== 测试完成 ===")
    print(f"  会话ID: {session_id}")
    print(f"  总轮次: {session.total_rounds}")
    print(f"  总体评分: {evaluation.overall_score}/10")
    print(f"  自然度: {evaluation.style_naturalness}/10")
    print(f"  难度适当性: {evaluation.difficulty_appropriateness}/10")
    print(f"  追问质量: {evaluation.follow_up_quality}/10")
    print(f"  话题覆盖: {evaluation.topic_coverage}/10")
    print(f"  优势: {', '.join(evaluation.strengths)}")
    print(f"  不足: {', '.join(evaluation.weaknesses)}")
    print(f"  评价: {evaluation.summary}")

    return session


def main() -> None:
    parser = argparse.ArgumentParser(description="Interview Tester - 测试面试 Agent 的表现")
    parser.add_argument("--domain", default="backend", help="面试领域 (default: backend)")
    parser.add_argument("--difficulty", default="mid", help="面试难度 junior/mid/senior (default: mid)")
    parser.add_argument("--candidate-level", default="mid", help="候选人水平 junior/mid/senior (default: mid)")
    parser.add_argument("--max-rounds", type=int, default=50, help="最大对话轮次 (default: 50)")
    args = parser.parse_args()

    config = TestConfig(
        domain=args.domain,
        difficulty=args.difficulty,
        candidate_level=args.candidate_level,
        max_rounds=args.max_rounds,
    )

    session = asyncio.run(run_test(config))
    saved_path = test_settings.data_dir / f"{session.session_id}.json"
    print(f"\n结果已保存: {saved_path}")


if __name__ == "__main__":
    main()
