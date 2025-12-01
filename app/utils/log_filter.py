import logging

class HealthCheckFilter(logging.Filter):
    """过滤健康检查请求的日志"""
    
    def filter(self, record):
        # 过滤健康检查路径的访问日志
        if hasattr(record, 'request_line') and '/health' in record.request_line:
            return False
        if hasattr(record, 'msg') and '/health' in str(record.msg):
            return False
        return True

class SensitiveDataFilter(logging.Filter):
    """过滤敏感信息"""
    
    SENSITIVE_FIELDS = ['password', 'token', 'authorization', 'secret', 'api_key']
    
    def filter(self, record):
        if hasattr(record, 'msg'):
            record.msg = self._mask_sensitive_data(str(record.msg))
        return True
    
    def _mask_sensitive_data(self, message):
        import re
        for field in self.SENSITIVE_FIELDS:
            pattern = rf'("{field}":\s*)"([^"]*)"'
            message = re.sub(pattern, rf'\1"***"', message, flags=re.IGNORECASE)
        return message