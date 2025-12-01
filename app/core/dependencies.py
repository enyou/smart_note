from functools import wraps
import inspect
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.services.auth_service import auth_service
from app.models.db_models import User
from app.utils.logger import get_logger

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user.
    Raises HTTPException if authentication fails.
    """
    user = await auth_service.get_current_user(db, credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 

def method_logger():
    """为方法添加开始和结束日志的依赖"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            # 获取方法信息
            method_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
            
            full_method_name = f"{class_name}.{method_name}" if class_name else method_name
            
            # 开始日志
            logger.info(
                f"METHOD START: {full_method_name}",
                method=full_method_name,
                stage="start"
            )
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                process_time = time.time() - start_time
                
                # 结束日志
                logger.info(
                    f"METHOD END: {full_method_name}",
                    method=full_method_name,
                    stage="end",
                    process_time=f"{process_time:.3f}s",
                    success=True
                )
                return result
                
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"METHOD ERROR: {full_method_name}",
                    method=full_method_name,
                    stage="error",
                    process_time=f"{process_time:.3f}s",
                    error=str(e),
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            method_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
            
            full_method_name = f"{class_name}.{method_name}" if class_name else method_name
            
            logger.info(
                f"METHOD START: {full_method_name}",
                method=full_method_name,
                stage="start"
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                process_time = time.time() - start_time
                
                logger.info(
                    f"METHOD END: {full_method_name}",
                    method=full_method_name,
                    stage="end",
                    process_time=f"{process_time:.3f}s",
                    success=True
                )
                return result
                
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"METHOD ERROR: {full_method_name}",
                    method=full_method_name,
                    stage="error",
                    process_time=f"{process_time:.3f}s",
                    error=str(e),
                    exc_info=True
                )
                raise
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator