#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: chat.py
功能: AI助手的聊天路由
作者: Yang
创建日期: 2025-06-16
版本号: 1.0
变更说明: 无
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.chat import ChatRequest
from app.services.chat_service import chat_service
from app.core.dependencies import method_logger
from app.utils.logger import get_logger


logger = get_logger(__name__)

router = APIRouter()


@method_logger
@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_session)):
    """
    与AI助手对话

    Args:
        request: ChatRequest模型数据
        db: 数据库连接实例

    Request:
        StreamingResponse: AI的回复内容
    """

    session_id = "{}_{}".format(request.user_id, request.note_id)
    logger.info(f"与AI助手对话 session id {session_id}")
    return StreamingResponse(chat_service.generate_stream_by_langchain(db, user_msg=request.user_msg, session_id=session_id), media_type="text/event-stream")
