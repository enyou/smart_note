# app/errors.py

class ErrorMessages:
    # 通用错误
    INTERNAL_SERVER_ERROR = "服务器内部错误"
    # 请求验证错误
    VALIDATION_ERROR = "请求数据验证失败,提供的数据不符合 API 要求。"
    # 资源未找到
    NOT_FOUND = "请求的资源在服务器中不存在。"
    # 认证错误
    UNAUTHORIZED = "您没有访问此资源的权限。"
    # 权限错误
    FORBIDDEN = "您没有权限访问此资源。"

    # 大模型错误
    LLM_CALLING_ERROR = "系统出现异常了。。请稍后重试！"
    LLM_CONN_TIMEOUT = "大模型服务连接超时，请检测你网络"

class CommonMessages:

    #大模型
    LLM_PROCESS_FINISH = "***完了***\n\n"
