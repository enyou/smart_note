from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.loggin_config import setup_logging
from app.db.vector_db_helper import ChromaLangChainManager
from app.middleware.logging_middleware import LoggingMiddleware
from app.router import api_router
from app.db.init_db import init_db
from app.llm.graph import builder
from langgraph.checkpoint.memory import MemorySaver

from app.utils.logger import get_logger

# 设置日志配置
setup_logging(settings.log_path, settings.log_level)
logger = get_logger('app')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    logger.info("Database Initialized")
    # 定义全局变量 sessions
    app.state.sessions = {}
    logger.info("App started, sessions initialized")

    # 加载向量数据库
    logger.info("loading vector")
    chroma = ChromaLangChainManager()
    app.state.chroma = chroma
    app.state.vector_store = chroma.load_existing_collection()

    # 启动graph
    checkpointer = MemorySaver()
    app.state.graph = builder.compile(checkpointer=checkpointer)

    logger.info("App started, graph initialized")
    yield

    # 关闭时执行（可选）
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    dependencies=[Depends(get_current_user)],
    lifespan=lifespan
)
# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware, exclude_paths=['/health', '/metrics'])
 
# 注册自定义异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 加载路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Smart Note API"}
