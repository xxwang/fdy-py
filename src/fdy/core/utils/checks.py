"""类型判断与安全转换。"""

from collections.abc import Callable, Iterable, Sized
from typing import Any

__all__ = [
    "ensure_list",
    "is_blank",
    "is_empty",
    "is_iterable",
    "safe_cast",
    "to_bool",
    "to_float",
    "to_int",
]

_TRUE_VALUES = frozenset({"1", "true", "t", "yes", "y", "on"})
_FALSE_VALUES = frozenset({"0", "false", "f", "no", "n", "off", "none", "null", ""})


def to_bool(value: Any) -> bool:
    """把常见真值表示转为 bool，无法识别的字符串按非空即真处理。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    return bool(value)


def to_int(value: Any, default: int = 0) -> int:
    """转为 int，失败返回 default；小数部分直接截断，整数型字符串含 "1e2" 也可解析。"""
    try:
        return int(float(value))
    except TypeError, ValueError:
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    """转为 float，失败返回 default。"""
    try:
        return float(value)
    except TypeError, ValueError:
        return default


def safe_cast[T](
    value: Any, target: Callable[[Any], T], default: T | None = None
) -> T | None:
    """调用 target(value) 做转换，抛类型或取值异常时返回 default。"""
    try:
        return target(value)
    except TypeError, ValueError:
        return default


def is_empty(value: Any) -> bool:
    """None、空字符串、空序列/字典/集合视为空；0、False 不算空。"""
    if value is None:
        return True
    if isinstance(value, Sized):
        return len(value) == 0
    return False


def is_blank(value: Any) -> bool:
    """None 或纯空白字符串视为空白。"""
    return value is None or not str(value).strip()


def is_iterable(value: Any) -> bool:
    """判断是否可迭代，字符串与字节按标量处理返回 False，避免逐字符遍历。"""
    if isinstance(value, (str, bytes)):
        return False
    return isinstance(value, Iterable)


def ensure_list(value: Any) -> list:
    """None 返回空列表，列表原样返回，字符串按单元素处理，其余可迭代对象转为列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return [value]
    return list(value)
