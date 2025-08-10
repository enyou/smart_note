import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# 确保 OpenAI API 密钥正确读取
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 未设置，请检查环境变量。")

# 初始化 OpenAI GPT 模型
llm = ChatOpenAI(
    api_key=api_key,
    base_url=os.getenv("OPENAI_API_URL"),
    model="deepseek-chat",
    temperature=0.7,
    streaming=True
)
