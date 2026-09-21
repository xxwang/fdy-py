"""把 APIException 转换为统一响应结构的异常处理器。"""

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from fdy.core.exceptions.api_exception import APIException
from fdy.core.models.api_response import APIResponse

__all__ = [
    "api_exception_handler",
    "register_exception_handlers",
]


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """把 APIException 转成 {code, message, data} 结构的 JSON 响应。"""
    payload = APIResponse.fail(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """把 fdy 的异常处理器注册到 FastAPI 应用上。"""
    app.add_exception_handler(APIException, api_exception_handler)
