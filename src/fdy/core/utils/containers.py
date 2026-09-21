"""容器与迭代工具。"""

from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from typing import Any

__all__ = [
    "chunk",
    "deep_get",
    "deep_merge",
    "deep_set",
    "first",
    "flatten",
    "group_by",
    "invert",
    "last",
    "omit",
    "pick",
    "unique",
    "unique_by",
]


def deep_merge(base: Mapping, override: Mapping) -> dict:
    """递归合并两个字典，override 优先，返回新字典且不修改入参。"""
    result = dict(base)
    for key, value in override.items():
        current = result.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            result[key] = deep_merge(current, value)
        else:
            result[key] = value
    return result


def deep_get(data: Any, path: str, default: Any = None, sep: str = ".") -> Any:
    """按 "a.b.0" 这样的路径取值，任一层缺失即返回 default。

    路径以 sep 分隔，键中若含 sep 字符则无法正确取值。
    """
    if not path:
        return default
    current = data
    for key in str(path).split(sep):
        if isinstance(current, Mapping):
            if key not in current:
                return default
            current = current[key]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                current = current[int(key)]
            except ValueError, IndexError:
                return default
        else:
            return default
    return current


def deep_set(
    data: MutableMapping, path: str, value: Any, sep: str = "."
) -> MutableMapping:
    """按路径写入，中间层缺失或类型不符时自动创建为字典。

    路径以 sep 分隔，键中若含 sep 字符则无法正确写入。空路径抛 ValueError。
    """
    if not path:
        raise ValueError("path 不能为空")
    keys = str(path).split(sep)
    current = data
    for key in keys[:-1]:
        child = current.get(key)
        if not isinstance(child, MutableMapping):
            child = {}
            current[key] = child
        current = child
    current[keys[-1]] = value
    return data


def flatten(data: Mapping, sep: str = ".", prefix: str = "") -> dict:
    """把嵌套字典拍平成单层，键用 sep 连接，空字典保留为叶子。"""
    result: dict = {}
    for key, value in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else str(key)
        if isinstance(value, Mapping) and value:
            result.update(flatten(value, sep=sep, prefix=full_key))
        else:
            result[full_key] = value
    return result


def chunk[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """按固定长度切分序列，最后一块可能不足。"""
    if size <= 0:
        raise ValueError("size 必须大于 0")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def group_by[T, K](items: Iterable[T], key: Callable[[T], K]) -> dict[K, list[T]]:
    """按 key 函数分组，组内保持原顺序。"""
    groups: dict[K, list[T]] = {}
    for item in items:
        groups.setdefault(key(item), []).append(item)
    return groups


def unique[T](items: Iterable[T]) -> list[T]:
    """去重并保持首次出现的顺序，要求元素可哈希。"""
    return list(dict.fromkeys(items))


def unique_by[T](items: Iterable[T], key: Callable[[T], Hashable]) -> list[T]:
    """按 key 去重并保持首次出现的顺序。"""
    seen: set[Hashable] = set()
    result: list[T] = []
    for item in items:
        marker = key(item)
        if marker not in seen:
            seen.add(marker)
            result.append(item)
    return result


def first[T](items: Iterable[T], default: T | None = None) -> T | None:
    """取第一个元素，序列为空时返回 default。"""
    for item in items:
        return item
    return default


def last[T](items: Iterable[T], default: T | None = None) -> T | None:
    """取最后一个元素，序列为空时返回 default。"""
    result = default
    for item in items:
        result = item
    return result


def pick(data: Mapping, keys: Iterable) -> dict:
    """只保留指定的键，缺失的忽略。"""
    wanted = set(keys)
    return {key: value for key, value in data.items() if key in wanted}


def omit(data: Mapping, keys: Iterable) -> dict:
    """剔除指定的键。"""
    excluded = set(keys)
    return {key: value for key, value in data.items() if key not in excluded}


def invert(data: Mapping) -> dict:
    """键值互换，值重复时后者覆盖前者。值必须可哈希，否则抛 TypeError。"""
    return {value: key for key, value in data.items()}
