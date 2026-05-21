import json
import re

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from interview_agent.config import llm_settings

from .config import test_settings
from .schemas import Evaluation, TestSession


_EVALUATOR_PROMPT = """你是一位面试评估专家，请根据以下面试记录评估面试官（AI Agent）的表现。

面试配置：
- 面试领域：{domain}
- 设定难度：{difficulty}
- 候选人水平：{candidate_level}

面试记录：
{transcript}

请从以下5个维度评分（1-10分）：
1. style_naturalness：对话自然度，面试官的提问和回应是否自然流畅
2. difficulty_appropriateness：难度适当性，问题难度是否匹配设定难度和候选人水平
3. follow_up_quality：追问质量，面试官根据候选人回答进行追问的质量
4. topic_coverage：话题覆盖度，面试涉及的知识面广度
5. overall_score：总体评分，对面试官整体表现的综合评价

同时提供：
- strengths：面试官的优势（字符串列表）
- weaknesses：面试官的不足（字符串列表）
- summary：总体评价（一段话）
- improvement_suggestions：改进建议（可操作的建议列表）

请只返回JSON，不要添加其他文字。JSON格式如下：
{{
  "style_naturalness": <int>,
  "difficulty_appropriateness": <int>,
  "follow_up_quality": <int>,
  "topic_coverage": <int>,
  "overall_score": <int>,
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "summary": "...",
  "improvement_suggestions": ["...", "..."]
}}"""


def _build_transcript(session: TestSession) -> str:
    lines = []
    for qa in session.qa_pairs:
        lines.append(f"[第{qa.round}轮] 面试官：{qa.question}")
        lines.append(f"[第{qa.round}轮] 候选人：{qa.answer}")
    return "\n".join(lines)


def _parse_eval_json(text: str) -> dict:
    content = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
    if fence_match:
        content = fence_match.group(1).strip()
    return json.loads(content)


async def evaluate_session(session: TestSession) -> Evaluation:
    provider = llm_settings.get_provider()
    llm = ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
        temperature=test_settings.evaluator_temperature,
    )

    transcript = _build_transcript(session)
    prompt_text = _EVALUATOR_PROMPT.format(
        domain=session.config.domain,
        difficulty=session.config.difficulty,
        candidate_level=session.config.candidate_level,
        transcript=transcript,
    )

    messages = [
        SystemMessage(content="你是一个专业的面试评估系统，只输出JSON格式的评估结果。"),
        HumanMessage(content=prompt_text),
    ]

    try:
        response = await llm.ainvoke(messages)
        data = _parse_eval_json(response.content)
        return Evaluation(**data)
    except Exception:
        return Evaluation(
            style_naturalness=0,
            difficulty_appropriateness=0,
            follow_up_quality=0,
            topic_coverage=0,
            overall_score=0,
            strengths=[],
            weaknesses=[],
            summary="评估失败：无法解析评估结果。",
            improvement_suggestions=[],
        )
