import asyncio
from typing import AsyncGenerator
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from app.llm.llm_loader import llm as chat
from app.core.messages import ErrorMessages, CommonMessages
load_dotenv()


class AIResponse(BaseModel):
    """AI响应的基础模型"""
    content: str

class AIChatServiceLangchain:
    
    
    
    async def generate_stream_by_langchain(self, user_prompt: str) -> AsyncGenerator[str, None]:
        
        messages = [HumanMessage(content=user_prompt),
                    SystemMessage(content="你是一个聊天助手，请用严谨的语言回答用户的问题。")]
        try:
            # 使用异步生成器逐步返回响应
            async for chunk in chat.astream(messages):
                content = chunk.content
                if content is not None:
                    yield f"data: {content}\n\n"
                    await asyncio.sleep(0.02)  # 控制流的速度
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

class AIChatService:
    
    # 构建消息历史
    # def build_messages(db: Session, session_id: str) -> list:
    #     # 从数据库获取历史消息
    #     db_conversations = crud.get_conversations_by_session(db, session_id)
        
    #     messages = [SystemMessage(content="You are a helpful AI assistant.")]
        
    #     for conv in reversed(db_conversations):  # 从旧到新排序
    #         messages.append(HumanMessage(content=conv.user_message))
    #         messages.append(SystemMessage(content=conv.ai_message))
    
    #     return messages 

    async def generate_stream_by_langchain(self, user_prompt: str) -> AsyncGenerator[str, None]:
        
        messages = [HumanMessage(content=user_prompt),
                    SystemMessage(content="你是一个聊天助手，请用严谨的语言回答用户的问题。")]
        try:
            # 使用异步生成器逐步返回响应
            async for chunk in chat.astream(messages):
                content = chunk.content
                if content is not None:
                    yield f"{content}"
                    await asyncio.sleep(0.02)  # 控制流的速度
        except Exception as e:
            yield ErrorMessages.LLM_CALLING_ERROR
        finally:
            yield CommonMessages.LLM_PROCESS_FINISH

# Global instance
ai_chat_service = AIChatService()
