"""fdy 的通用部分 —— 不依赖任何 Web / GUI 框架。

这里只放框架无关的能力：`utils`（工具函数）、`models`（数据模型）、
`exceptions`（业务异常）。FastAPI 与 PySide6 的集成在 `fdy.web` / `fdy.gui`，
它们只单向依赖本包，core 不反向依赖它们。

对外仍由顶层 `fdy` 重导出全部符号；`fdy.core` 自身也是自洽的入口，
`from fdy.core import snake_case` 与 `from fdy.core.utils.dates import date_range`
都能直接用。
"""

from . import exceptions, models, utils
from .exceptions.api_exception import APIException
from .models.api_response import APIResponse
from .utils import *  # noqa: F403

__all__ = [
    *utils.__all__,
    "APIException",
    "APIResponse",
    "exceptions",
    "models",
    "utils",
]
