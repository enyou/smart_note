#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: gen_study_plan_agent.py
功能: 构建一个创建学习计划的Agent
作者: Yang
创建日期: 2025-06-12
版本号: 1.0
变更说明: 无
"""

from langchain.agents import initialize_agent
from langchain.agents import AgentType, AgentExecutor

from app.llm.tools.ext_input_key_tool import ExtInputKeyTool
from app.llm.tools.generate_plan_tool import GeneratePlanTool
from app.llm.tools.qa_tool import QATool
from app.llm.tools.save_plan_to_db import SavePlanToDBTool
from app.llm.tools.task_classifier_tool import TaskClassiflerTool
from app.llm.llm_loader import llm

# 初始化工具
tools = [
    TaskClassiflerTool(),
    ExtInputKeyTool(),
    QATool(),
    GeneratePlanTool(),
    SavePlanToDBTool()
]

# 定义一个 agent 用于处理任务
agent = initialize_agent(
    tools=tools,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    llm=llm,
    verbose=True
)
# agent_executor = AgentExecutor.from_agent_and_tools(
#     agent=agent,
#     tools=tools,
#     verbose=True
# )

# 示例使用
if __name__ == "__main__":
    # user_input = input("请输入你的问题或学习需求：")
    result = agent.run("我想要学习java")
    print(result)
