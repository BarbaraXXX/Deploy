from pydantic import BaseModel, Field


class InterviewProfile(BaseModel):
    company: str = Field(description="公司名称")
    position: str = Field(description="岗位名称")
    difficulty_tendency: str = Field(default="mid", description="难度倾向: junior/mid/senior")
    focus_areas: list[str] = Field(default_factory=list, description="考查重点领域列表")
    interview_style: str = Field(default="", description="面试风格描述，Agent学习此风格")
    question_types: list[str] = Field(default_factory=list, description="常见问题类型，如['原理题','系统设计','场景题']")
    key_traits: list[str] = Field(default_factory=list, description="区分性特征，如['偏底层','算法题少','追细节']")
    source_count: int = Field(default=0, description="聚合来源面经数量")


class InterviewExperience(BaseModel):
    company: str = Field(description="公司名称", max_length=128)
    position: str = Field(description="岗位名称", max_length=128)
    raw_text: str = Field(default="", description="面经原始文本，任意格式，可以是博客文章、笔记、回忆帖等", max_length=100000)
