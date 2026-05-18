from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from interview_agent.config import LLMProviderConfig, llm_settings
from interview_agent.mcp_client import get_mcp_tools
from interview_agent.prompts import build_system_prompt


def _create_llm(tools: list, provider: LLMProviderConfig) -> ChatOpenAI:
    llm = ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        model=provider.model,
        temperature=0.7,
    )
    if tools:
        llm = llm.bind_tools(tools)
    return llm


def _llm_call(state: MessagesState, *, llm: ChatOpenAI, system_prompt: str) -> dict:
    system = SystemMessage(content=system_prompt)
    response = llm.invoke([system] + state["messages"])
    return {"messages": [response]}


def _should_continue(state: MessagesState) -> Literal["tools", END]:
    return tools_condition(state)


async def build_interview_agent(
    domain: str, difficulty: str, provider_name: str | None = None
) -> Runnable:
    provider = llm_settings.get_provider(provider_name)
    tools = await get_mcp_tools()
    llm = _create_llm(tools, provider)
    system_prompt = build_system_prompt(domain, difficulty)

    graph = StateGraph(MessagesState)

    graph.add_node(
        "interviewer",
        lambda state: _llm_call(state, llm=llm, system_prompt=system_prompt),
    )

    if tools:
        graph.add_node("tools", ToolNode(tools))
        graph.add_conditional_edges("interviewer", _should_continue, ["tools", END])
        graph.add_edge("tools", "interviewer")
    else:
        graph.add_edge("interviewer", END)

    graph.add_edge(START, "interviewer")

    return graph.compile()
