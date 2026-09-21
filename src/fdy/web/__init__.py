"""FastAPI 集成（需 fdy[web]）。"""

from ..core._optional import require

require("fastapi")

# 可选依赖必须先校验，故 handlers 的导入不能提到文件顶部
from . import handlers  # noqa: E402
from .handlers import api_exception_handler, register_exception_handlers  # noqa: E402

__all__ = [
    "api_exception_handler",
    "handlers",
    "register_exception_handlers",
]
