import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
import httpx
import os
from fastapi import HTTPException
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

from app.core.messages import ErrorMessages
load_dotenv()


class AIResponse(BaseModel):
    """AI响应的基础模型"""
    content: str


class AIService:

    async def generate_response(self, system_prompt: str, user_prompt: str) -> AIResponse:
        """调用大模型API生成响应"""
        try:
            # # 设置代理
            # os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
            # os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

            # 初始化 OpenAI 客户端
            client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_URL")
            )
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                stream=False
            )
            content = response.choices[0].message.content
            return AIResponse(
                content=content
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=ErrorMessages.LLM_CONN_TIMEOUT
            )
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"{ErrorMessages.LLM_CALLING_ERROR}: {str(e)}"
            )

    async def generate_stream_response(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """调用大模型API生成流式响应"""
        try:
            client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_URL")
            )
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                stream=True
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    await asyncio.sleep(0.02)  # 控制流的速度

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=ErrorMessages.LLM_CONN_TIMEOUT
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"{ErrorMessages.LLM_CALLING_ERROR}: {str(e)}"
            )


# Global instance
ai_service = AIService()
