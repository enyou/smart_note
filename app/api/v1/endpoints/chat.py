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
from app.llm.chat_service import ai_chat_service

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_session)):
    """与AI助手对话"""
    session_id = "{}_{}".format(request.user_id, request.note_id)
    return StreamingResponse(chat_service.generate_stream_by_langchain(db, user_msg=request.user_msg,session_id=session_id), media_type="text/event-stream")
    # return await chat_service.chat_response(db=db, user_msg=request.user_msg)


@router.post("/chat_common")
async def chat_common(request: ChatRequest,db: AsyncSession = Depends(get_session)):
    """与AI助手对话"""
    return StreamingResponse(ai_chat_service.generate_stream_by_langchain(user_prompt=request.user_msg), media_type="text/event-stream")
    # return await chat_service.chat_response(db=db, user_msg=request.user_msg)
