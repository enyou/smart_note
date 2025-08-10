#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: conversation.py
功能: 聊天助手的历史会话记录
作者: Yang
创建日期: 2025-07-22
版本号: 1.0
变更说明: 无
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ConversationBase(BaseModel):
    session_id: str
    user_message: str
    ai_message: str
    metadata: Optional[Dict] = None


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ChatRequest(BaseModel):
    message: str
    session_id: str  # 客户端生成的会话ID
    metadata: Optional[Dict] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    conversation_id: int
