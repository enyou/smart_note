import logging
from contextvars import ContextVar
import uuid
from typing import Optional, Dict, Any

# 请求上下文变量
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class RequestContextFilter(logging.Filter):
    """为日志记录添加请求上下文信息"""
    
    def filter(self, record):
        record.request_id = request_id_var.get() or 'system'
        record.user_id = user_id_var.get() or 'anonymous'
        return True

class AppLogger:
    """应用日志记录器封装"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.addFilter(RequestContextFilter())
    
    def _extra_fields(self, **kwargs) -> Dict[str, Any]:
        """构建额外的日志字段"""
        extra = {
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            **kwargs
        }
        return extra
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=self._extra_fields(**kwargs))
    
    def error(self, msg: str, exc_info=True, **kwargs):
        self.logger.error(msg, exc_info=exc_info, extra=self._extra_fields(**kwargs))
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=self._extra_fields(**kwargs))
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=self._extra_fields(**kwargs))
    
    def metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """记录监控指标"""
        metric_logger = logging.getLogger('metrics')
        metric_data = {
            'metric': metric_name,
            'value': value,
            'tags': tags or {},
            'timestamp': logging.time()
        }
        metric_logger.info('metric', extra=metric_data)

def get_logger(name: str) -> AppLogger:
    """获取应用日志记录器"""
    return AppLogger(name)