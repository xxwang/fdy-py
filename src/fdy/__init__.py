"""fdy —— 日常开发工具库。"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

from .core import exceptions, models, utils
from .core.exceptions.api_exception import APIException
from .core.models.api_response import APIResponse
from .core.utils import *  # noqa: F403

try:
    __version__ = _package_version("fdy")
except PackageNotFoundError:  # 源码目录未安装时兜底
    __version__ = "0.0.0"

__all__ = [
    *utils.__all__,
    "__version__",
    "models",
    "exceptions",
    "utils",
    "APIResponse",
    "APIException",
]
