"""可选依赖的延迟加载，统一给出可执行的安装提示。"""

from importlib import import_module
from typing import Any

__all__ = ["require"]

_EXTRA_OF: dict[str, str] = {
    "PySide6": "gui",
    "fastapi": "web",
    "httpx": "http",
    "starlette": "web",
}


def require(module: str) -> Any:
    """按需导入可选依赖，缺失时抛出带安装命令的 ImportError。"""
    try:
        return import_module(module)
    except ImportError as exc:
        hint = _install_hint(module)
        raise ImportError(f"fdy 的该功能需要 {module}，请先安装：{hint}") from exc


def _install_hint(module: str) -> str:
    extra = _EXTRA_OF.get(module)
    return f'pip install "fdy[{extra}]"' if extra else f"pip install {module}"
