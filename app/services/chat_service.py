import asyncio
from typing import AsyncGenerator
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.llm_loader import llm as chat
from app.core.messages import ErrorMessages, CommonMessages
from app.services.conversation_service import conversation_service
from app.models import conversation as conv_model
from app.core.dependencies import method_logger
from app.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class AIResponse(BaseModel):
    """AI响应的基础模型"""
    content: str


class AIChatService:

    # 构建消息历史
    @method_logger
    async def build_messages(self, db: AsyncSession, session_id: str) -> list:
        logger.info("从数据库获取历史消息")
        db_conversations = await conversation_service.get_conversations_by_session(db, session_id)

        messages = [SystemMessage(content="你是一个聊天助手，请用严谨的语言回答用户的问题。")]

        for conv in reversed(db_conversations):  # 从旧到新排序
            messages.append(HumanMessage(content=conv.user_message))
            messages.append(SystemMessage(content=conv.ai_message))

        return messages

    @method_logger
    async def generate_stream_by_langchain(self, db: AsyncSession, user_msg: str, session_id: str, meta_data: str = None) -> AsyncGenerator[str, None]:
        messages = await self.build_messages(db, session_id)
        messages.append(HumanMessage(content=user_msg))
        full_response = ""
        try:
            # 使用异步生成器逐步返回响应
            async for chunk in chat.astream(messages):
                content = chunk.content
                if content is not None:
                    full_response += content
                    yield f"{content}"
                    await asyncio.sleep(0.02)  # 控制流的速度
        except Exception as e:
            logger.error(str(e))
            yield ErrorMessages.LLM_CALLING_ERROR
        finally:
            logger.info("保存完整对话到数据库")
            conversation = conv_model.ConversationCreate(
                session_id=session_id,
                user_message=user_msg,
                ai_message=full_response,
                metadata_data=meta_data
            )
            await conversation_service.create_conversation(db, conversation)
            yield CommonMessages.LLM_PROCESS_FINISH


# Global instance
chat_service = AIChatService()
