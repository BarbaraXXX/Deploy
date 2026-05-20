from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from interview_agent.config import LLMProviderConfig

logger = logging.getLogger(__name__)

_JD_SYSTEM_PROMPT = (
    "你是一个职位描述分析助手。请从以下岗位JD中提取关键信息，并以JSON格式返回。\n\n"
    "要求提取的字段：\n"
    "- position_title: 岗位名称\n"
    "- required_skills: 必需技能列表（字符串数组）\n"
    "- required_experience: 经验要求描述\n"
    "- key_responsibilities: 核心职责列表（字符串数组）\n"
    "- preferred_qualifications: 加分项列表（字符串数组）\n"
    "- tech_stack: 涉及的技术栈列表（字符串数组）\n"
    "- interview_focus: 基于以上分析，给出该岗位面试应重点考察的方向和建议\n\n"
    "请只返回JSON，不要添加任何其他文字。"
)

_MAX_JD_LENGTH = 4000


class StructuredJD(BaseModel):
    position_title: str = Field(default="", description="岗位名称", max_length=128)
    required_skills: list[str] = Field(default_factory=list, description="必需技能列表", max_length=20)
    required_experience: str = Field(default="", description="经验要求，如'3-5年后端开发经验'", max_length=256)
    key_responsibilities: list[str] = Field(default_factory=list, description="核心职责列表", max_length=20)
    preferred_qualifications: list[str] = Field(default_factory=list, description="加分项列表", max_length=20)
    tech_stack: list[str] = Field(default_factory=list, description="技术栈列表", max_length=20)
    interview_focus: str = Field(
        default="",
        description="面试侧重点建议，LLM根据JD分析该岗位面试应重点考察的方向",
        max_length=512,
    )


async def parse_jd(raw_jd: str, provider: LLMProviderConfig) -> StructuredJD | None:
    text = raw_jd.strip()
    if not text:
        return None
    if len(text) > _MAX_JD_LENGTH:
        text = text[:_MAX_JD_LENGTH]

    llm = ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
        temperature=0,
    )

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_JD_SYSTEM_PROMPT),
                HumanMessage(content=text),
            ]
        )
        content = response.content if isinstance(response.content, str) else str(response.content)
        data = json.loads(content)
        return StructuredJD.model_validate(data)
    except Exception:
        logger.warning("Failed to parse JD via LLM", exc_info=True)
        return None
