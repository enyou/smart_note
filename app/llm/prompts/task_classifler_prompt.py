#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: task_classifler_prompt.py
功能: 提示词，用来判断是学习计划生成还是普通的提问
作者: Yang
创建日期: 2025-06-12
版本号: 1.0
变更说明: 无
"""

class TaskClassiflerPrompt:
    
    PROMPT = """你是一个智能助手，擅长分析用户的提问目的。现在请根据用户的输入判断其意图属于以下两类之一：
                    1. 学习意图（Learning Intent）：用户希望系统地学习某个技能或知识，希望获取教程、学习路径、练习方法等。
                    2. 问题疑问（Questioning Intent）：用户对某个概念、现象或问题感到疑惑，期望你解释或解答。
                    请你只输出：
                    - “学习意图”
                    - 或
                    - “问题疑问”
                    用户输入：{question}
                    你的判断：
            """
