from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from interview_agent.config import llm_settings

from .config import test_settings


def build_candidate_llm(candidate_level: str) -> ChatOpenAI:
    provider = llm_settings.get_provider()
    return ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
        temperature=test_settings.candidate_temperature,
    )


def get_candidate_system_prompt(domain: str, candidate_level: str) -> str:
    level_map = {
        "junior": "1-3年",
        "mid": "3-5年",
        "senior": "5年以上",
    }
    experience = level_map.get(candidate_level, "3-5年")

    level_guidance = {
        "junior": (
            "你的回答应该比较简单直接，展示基础知识的掌握，但不需要涉及太深层的架构设计。"
            "偶尔可以对一些高级问题表现出不太确定。"
        ),
        "mid": (
            "你的回答应该展示扎实的技术功底和实际项目经验，能够深入分析问题，"
            "但偶尔在某些前沿领域或复杂架构问题上可以表现出需要思考。"
        ),
        "senior": (
            "你的回答应该深入且全面，展示丰富的架构设计经验和技术决策能力，"
            "能够从多个维度分析问题，给出系统性的解决方案。"
        ),
    }
    guidance = level_guidance.get(candidate_level, level_guidance["mid"])

    return (
        f"你是一名正在参加{domain}领域技术面试的候选人，拥有{experience}工作经验。\n\n"
        f"{guidance}\n\n"
        "面试规则：\n"
        "- 以自然的方式回答面试官的问题，像一个真实的候选人\n"
        "- 保持角色，永远不要打破模拟，不要提及自己是AI或语言模型\n"
        "- 不要反问面试官问题，只回答并等待下一个问题\n"
        "- 回答的深度和广度应该符合你的经验水平\n"
        f"- 你面试的领域是{domain}，请展示该领域的相关技术知识\n"
    )


async def generate_candidate_response(
    messages: list[BaseMessage],
    candidate_llm: ChatOpenAI,
    candidate_prompt: str,
) -> str:
    system = SystemMessage(content=candidate_prompt)
    response = await candidate_llm.ainvoke([system] + messages)
    return response.content
