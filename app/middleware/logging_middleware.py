# middleware/logging_middleware.py
import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import request_id_var, user_id_var, get_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics']
        self.logger = get_logger('middleware')
        self.access_logger = logging.getLogger('uvicorn.access')
    
    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查等路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 生成请求ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # 尝试从认证信息中获取用户ID
        user_id = self._get_user_id(request)
        user_id_var.set(user_id)
        
        # 记录请求开始
        start_time = time.time()
        self.logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else 'unknown'
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录访问日志
            self._log_access(request, response, process_time, user_id)
            
            # 记录请求完成
            self.logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            self.logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                process_time=process_time,
                exc_info=True
            )
            raise
    
    def _get_user_id(self, request: Request) -> str:
        """从请求中获取用户ID"""
        # 这里可以根据你的认证系统实现
        # 例如从 JWT token 或 session 中获取
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # 解析 token 获取用户ID
            # token = auth_header[7:]
            # user_id = decode_token(token).get('user_id')
            return 'user-from-token'  # 示例
        return 'anonymous'
    
    def _log_access(self, request: Request, response: Response, process_time: float, user_id: str):
        """记录访问日志"""
        client_addr = request.client.host if request.client else 'unknown'
        request_line = f"{request.method} {request.url.path} HTTP/1.1"
        
        # 使用 uvicorn.access 记录器记录标准访问日志
        self.access_logger.info(
            "",
            extra={
                'client_addr': client_addr,
                'request_line': request_line,
                'status_code': response.status_code,
                'user_id': user_id,
                'process_time': process_time
            }
        )