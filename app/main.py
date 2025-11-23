from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.db.vector_db_helper import ChromaLangChainManager
from app.router import api_router
from app.db.init_db import init_db
from app.llm.graph import builder
from langgraph.checkpoint.memory import MemorySaver



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    print("Database Initialized")
    # 定义全局变量 sessions
    app.state.sessions = {}
    print("App started, sessions initialized")

    # 加载向量数据库
    print("loading vector")
    chroma = ChromaLangChainManager()
    app.state.chroma = chroma
    app.state.vector_store = chroma.load_existing_collection()

    # 启动graph
    checkpointer = MemorySaver()
    app.state.graph = builder.compile(checkpointer=checkpointer)

    print("App started, graph initialized")
    yield

    # 关闭时执行（可选）
    print("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# 注册自定义异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 加载路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Smart Note API"}
