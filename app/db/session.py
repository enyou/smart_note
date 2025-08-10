from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
print(settings.SQLALCHEMY_DATABASE_URI)
# 创建异步引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=True,  # 开发时显示SQL语句
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()

# 依赖注入: 获取数据库会话


async def get_session():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
