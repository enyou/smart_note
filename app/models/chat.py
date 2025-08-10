#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: chat.py
功能: chat 模型
作者: Yang
创建日期: 2025-06-16
版本号: 1.0
变更说明: 无
"""
from datetime import datetime
from pydantic import BaseModel


class ChatBase(BaseModel):
    user_id: int
    note_id: int
    conversation_num: int
    system_msg: str
    user_msg: str
    conversation_datetime: datetime


class ChatRequest(BaseModel):
    user_msg: str
    user_id: int
    note_id: int


class ChatResponse(BaseModel):
    system_msg: str
