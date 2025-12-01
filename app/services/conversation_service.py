#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: conversation_service.py
功能: 管理converstaion这张表的CRUD
作者: Yang
创建日期: 2025-07-22
版本号: 1.0
变更说明: 无
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import db_models, conversation
from app.core.dependencies import method_logger
from app.utils.logger import get_logger


logger = get_logger(__name__)


class ConversationService:

    @method_logger
    async def create_conversation(self, db: AsyncSession, conversation: conversation.ConversationCreate):
        db_conversation = db_models.Conversation(
            session_id=conversation.session_id,
            user_message=conversation.user_message,
            ai_message=conversation.ai_message,
            metadata=conversation.metadata
        )
        db.add(db_conversation)
        await db.commit()
        return

    @method_logger
    async def get_conversations_by_session(self, db: AsyncSession, session_id: str, limit: int = 100):
        stmt = select(db_models.Conversation).where(db_models.Conversation.session_id ==
                                                    session_id).order_by(db_models.Conversation.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


conversation_service = ConversationService()
