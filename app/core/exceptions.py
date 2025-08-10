# app/exceptions.py
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Request

# 自定义 HTTPException 异常处理器
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.status_code,
            "message": exc.detail,
            "details": "这是一条更详细的错误描述"
        }
    )

# 自定义请求验证异常处理器
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error_code": 400,
            "message": "请求数据验证失败",
            "errors": exc.errors(),
            "body": exc.body.decode("utf-8")
        }
    )
