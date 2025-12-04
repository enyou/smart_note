#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: graph.py
功能: 基于langgraph的agent
作者: Yang
创建日期: 2025-09-13
版本号: 1.0
变更说明: 无
"""
from typing import Annotated, List, Optional, Literal, TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.messages.ai import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
from app.llm.llm_loader import llm
from app.llm.prompts.check_input_completeness_prompt import CheckInputCompletenessPrompt
from app.llm.prompts.gen_plan_prompt import GenPlanPrompt
from app.services.study_plan_service import study_plan_service

from app.core.dependencies import method_logger
from app.utils.logger import get_logger


logger = get_logger(__name__)
# 定义状态


class State(TypedDict):
    # 用户输入的学习内容
    subject: str
    # 输入的内容是否完整
    input_completeness: Optional[bool] = None
    # 曾经创建的学习计划
    history_plan: str
    # 是否曾经学习过
    learned_before: Optional[bool] = None
    # 是否要深入学习
    want_deep_learn: Optional[bool] = None
    # 生成的学习计划
    learning_plan: Optional[str] = None
    # 用户是否满意
    is_satisfied: Optional[bool] = None
    # 当前状态
    status: str = "start"
    messages: Annotated[List, add_messages]  # 关键：使用 Annotated 和 add_messages


@method_logger
def check_input_info(subject: str) -> bool:
    """
    检查用户输入的信息是否完整。
    """
    logger.info("检查用户输入的信息是否完整")
    prompt = ChatPromptTemplate.from_template(
        CheckInputCompletenessPrompt.PROMPT)
    chains = prompt | llm
    response = chains.invoke(input=subject)
    return response.content

# RAG检索函数


@method_logger
def retrieve_learning_history(subject: str, vectorstore) -> str:
    """
    检查用户是否曾经学习过该主题。如果学习过该主题，则返回学习过的内容。
    """
    logger.info("检查用户是否曾经学习过该主题")
    docs = vectorstore.similarity_search_with_score(subject, k=3)
    contexts = [doc[0].page_content for doc in docs if doc[1] > 7]
    return "\n".join(contexts)


# 生成学习计划函数
@method_logger
def generate_learning_plan(subject: str, history_study_plan: str, level: Literal["beginner", "advanced"]) -> str:
    """生成学习计划"""
    logger.info(f"生成学习计划, 计划主题:{subject}, 当前水平: {level}")
    input = {"subject": subject}
    if level == "beginner":
        prompt_template = ChatPromptTemplate.from_template(
            GenPlanPrompt.PROMPT_WITHOUT_HISTORY)
    else:
        prompt_template = PromptTemplate(
            input_variables=["history_study_plan", "subject"],
            template=GenPlanPrompt.PROMPT_WITH_HISTORY
        )
        input["history_study_plan"] = history_study_plan
    chains = prompt_template | llm
    response = chains.invoke(input=input)
    return response.content

# 定义各个节点


@method_logger
def check_input_completeness_node(state: State) -> State:
    """查用户输入的信息是否完整节点"""
    logger.info("检查户输入的信息是否完整节点")

    result = check_input_info(state["messages"][-1])
    is_completeness = False
    if result == "是":
        is_completeness = True
    if not is_completeness:
        return {
            "status": "checking_input_completeness",
            "input_completeness": False,
            "messages": state["messages"] + [
                AIMessage(
                    content=f"您输入的信息较少，请输入更多的信息。如目标和当前的水平。例如：我想要学习python，我没有任何基础，通过学习能够完成简单的编程")
            ]
        }
    return {
        "input_completeness": True,
        "status": "retrieve"
    }


@method_logger
def retrieve_node(state: State, config) -> State:
    """检索学习历史节点"""
    logger.info("检索学习历史节点")
    vector_store = config["configurable"].get("vector_store")
    result = retrieve_learning_history(state["subject"], vector_store)
    has_learned = False
    if result:
        has_learned = True
    return {"learned_before": has_learned, "status": "retrieved",  "history_plan": result}


@method_logger
def ask_deep_learn_node(state: State) -> State:
    """询问是否深入学习节点"""
    logger.info("询问是否深入学习节点")
    logger.info(f"之前是否学习过:{state["learned_before"]}")
    if state["learned_before"]:
        return {
            "status": "asking_deep_learn",
            "messages": state["messages"] + [
                AIMessage(
                    content=f"检测到您曾经学习过如下内容：\n\n'{state['history_plan']}'\n\n您是否希望在此基础上进行深入学习？")
            ]
        }
    else:
        return {"status": "generate_beginner_plan"}


@method_logger
def handle_deep_learn_response_node(state: State) -> State:
    """处理用户是否深入学习的响应"""
    logger.info("处理用户是否深入学习的响应节点:")
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        response = last_message.content.lower()
        if "是" in response or "yes" in response or "想" in response:
            return {"want_deep_learn": True, "status": "generate_advanced_plan"}
        else:
            return {"want_deep_learn": False, "status": "generate_beginner_plan"}
    return {"status": "generate_beginner_plan"}


@method_logger
def generate_plan_node(state: State) -> State:
    """生成学习计划节点"""
    logger.info("生成学习计划节点")
    if state.get("want_deep_learn", False) or (state["learned_before"] and state.get("want_deep_learn", True)):
        level = "advanced"
    else:
        level = "beginner"

    logger.info(f"正在生成{'进阶' if level == 'advanced' else '初级'}学习计划...")
    plan = generate_learning_plan(
        state["subject"], state['history_plan'], level)

    return {
        "learning_plan": plan,
        "status": "presenting_plan",
        "messages": state["messages"] + [
            AIMessage(content=f"为您生成了一份{level}学习计划：\n\n{plan}\n\n您对这个计划满意吗？")
        ]
    }


@method_logger
def handle_feedback_node(state: State) -> State:
    """处理用户反馈节点"""
    logger.info("处理用户反馈节点")
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        response = last_message.content.lower()
        if "是" in response or "满意" in response or "yes" in response:
            return {"is_satisfied": True, "status": "save_plan"}
        else:
            return {"is_satisfied": False, "status": "adjust_plan"}
    return {"is_satisfied": False, "status": "adjust_plan"}


@method_logger
async def save_plan_node(state: State, config) -> State:
    """保存学习计划节点"""
    logger.info("保存学习计划节点")
    # 这里应该是实际保存到数据库的逻辑
    db_session = config["configurable"].get("db_session")
    plan = await study_plan_service.create_study_plan_from_ai_response(db_session, state["learning_plan"])
    chroma_db = config["configurable"].get("chroma")
    chroma_db.add_documents([Document(page_content=plan.content)])
    chroma_db.persist()
    return {
        "status": "end",
        "messages": state["messages"] + [
            AIMessage(content="学习计划已保存！祝您学习愉快！")
        ]
    }


@method_logger
def adjust_plan_node(state: State) -> State:
    """调整学习计划节点"""
    logger.info("调整学习计划节点")
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        feedback = last_message.content
        # 基于用户反馈重新生成计划
        # 确定当前级别
        level = "advanced" if state.get(
            "want_deep_learn", False) else "beginner"

        # 生成调整后的计划
        adjusted_plan = generate_learning_plan(
            f"{state['subject']}，根据反馈调整: {feedback}", state["history_plan"], level)

        return {
            "learning_plan": adjusted_plan,
            "status": "presenting_plan",
            "messages": state["messages"] + [
                AIMessage(
                    content=f"根据您的反馈，已调整学习计划：\n\n{adjusted_plan}\n\n您对这个调整后的计划满意吗？")
            ]
        }
    return state


# 创建图
builder = StateGraph(State)

# 添加节点
builder.add_node("retrieve", retrieve_node)
builder.add_node("check_input_completeness", check_input_completeness_node)
builder.add_node("ask_deep_learn", ask_deep_learn_node)
builder.add_node("handle_deep_learn_response", handle_deep_learn_response_node)
builder.add_node("generate_plan", generate_plan_node)
builder.add_node("handle_feedback", handle_feedback_node)
builder.add_node("save_plan", save_plan_node)
builder.add_node("adjust_plan", adjust_plan_node)

# 动态入口点函数


@method_logger
def get_entry_point(state: State) -> str:
    """根据状态动态决定入口点"""
    status = state.get("status")
    logger.info(f"当前状态:{status}")
    if status or not status or status == "checking_input_completeness":
        return "check_input_completeness"
    if status == "retrieve":
        return "retrieve"
    elif status == "asking_deep_learn":
        return "handle_deep_learn_response"
    elif status == "generate_beginner_plan" or status == "generate_advanced_plan":
        return "generate_plan"
    elif status == "presenting_plan":
        return "handle_feedback"
    elif status == "adjust_plan":
        return "adjust_plan"
    else:
        return "check_input_completeness"


# 设置动态入口点
builder.set_conditional_entry_point(get_entry_point)

# 添加边
builder.add_conditional_edges(
    "check_input_completeness",
    lambda state: state["status"],
    {
        "retrieve": "retrieve",
        "checking_input_completeness": "check_input_completeness"
    }
)
builder.add_edge("retrieve", "ask_deep_learn")
builder.add_conditional_edges(
    "ask_deep_learn",
    lambda state: state["status"],
    {
        "asking_deep_learn": "handle_deep_learn_response",
        "generate_beginner_plan": "generate_plan"
    }
)
builder.add_edge("handle_deep_learn_response", "generate_plan")
builder.add_edge("generate_plan", "handle_feedback")
builder.add_conditional_edges(
    "handle_feedback",
    lambda state: state["status"],
    {
        "save_plan": "save_plan",
        "adjust_plan": "adjust_plan"
    }
)
builder.add_edge("save_plan", END)
builder.add_edge("adjust_plan", "handle_feedback")
