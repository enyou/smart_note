import logging
import logging.config
import json
import os
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义 JSON 格式化器，用于结构化日志"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = self.formatTime(record)
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # 添加应用信息
        log_record['service'] = 'smart_note_app'

        # 添加代码位置信息
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno


def ensure_log_directory(log_path):
    """确保日志目录存在"""
    log_path = Path('./log/smart_note_app' if not log_path else log_path)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def get_log_level(log_level):
    """根据环境变量获取日志级别"""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(log_level, logging.INFO)


def setup_logging(log_path, log_level):
    """日志配置"""

    log_path = ensure_log_directory(log_path)
    log_level = get_log_level(log_level)

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': CustomJsonFormatter,
                'format': '%(timestamp)s %(level)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
            },
            'access': {
                'format': '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
            }
        },
        'handlers': {
            # JSON 格式控制台输出（用于容器环境）
            'json_console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json',
                'stream': sys.stdout
            },
            # 应用日志文件
            'app_file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'detailed',
                'filename': str(log_path / 'app.log'),
                'when': 'midnight',
                'interval': 1,
                'backupCount': 30,
                'encoding': 'utf-8'
            },
            # 错误日志文件
            'error_file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': logging.ERROR,
                'formatter': 'detailed',
                'filename': str(log_path / 'error.log'),
                'when': 'W0',  # 每周一滚动
                'backupCount': 8,
                'encoding': 'utf-8'
            },
            # 访问日志文件
            'access_file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'access',
                'filename': str(log_path / 'access.log'),
                'when': 'midnight',
                'backupCount': 30,
                'encoding': 'utf-8'
            },
            # 监控指标日志
            'metrics_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'json',
                'filename': str(log_path / 'metrics.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            '': {  # 根日志记录器
                'level': log_level,
                'handlers': ['json_console', 'app_file', 'error_file'],
                'propagate': False
            },
            'app': {  # 应用日志
                'level': log_level,
                'handlers': ['json_console', 'app_file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': logging.WARNING,
                'handlers': ['json_console', 'app_file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': logging.INFO,
                'handlers': ['access_file'],  # 访问日志单独处理
                'propagate': False
            },
            'uvicorn.error': {
                'level': logging.INFO,
                'handlers': ['json_console', 'app_file'],
                'propagate': False
            },
            'metrics': {  # 监控指标日志
                'level': logging.INFO,
                'handlers': ['metrics_file'],
                'propagate': False
            },
            # 数据库相关日志
            'sqlalchemy.engine': {
                'level': logging.WARNING,
                'handlers': ['json_console', 'app_file'],
                'propagate': False
            },
            # 第三方库日志控制
            'httpx': {
                'level': logging.WARNING,
                'handlers': ['json_console'],
                'propagate': False
            },
            'httpcore': {
                'level': logging.WARNING,
                'handlers': ['json_console'],
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)
