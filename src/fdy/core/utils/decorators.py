"""常用函数装饰器。"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

_logger = logging.getLogger("fdy")

__all__ = [
    "memoize",
    "retry",
    "silent",
    "singleton",
    "timer",
]


def timer(func: Callable | None = None, *, log: bool = True) -> Callable:
    """统计函数耗时，可用 @timer 或 @timer(log=False) 两种写法，耗时记录在 last_elapsed 上。"""

    def decorate(target: Callable) -> Callable:
        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            try:
                return target(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - started
                wrapper.last_elapsed = elapsed  # type: ignore[attr-defined]
                if log:
                    _logger.info("%s 耗时 %.4fs", target.__qualname__, elapsed)

        wrapper.last_elapsed = 0.0  # type: ignore[attr-defined]
        return wrapper

    return decorate(func) if func is not None else decorate


def retry(
    times: int = 3,
    delay: float = 0.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    logger: logging.Logger | None = None,
) -> Callable:
    """失败后重试，times 为总尝试次数，delay 按 backoff 逐次放大。"""
    if times < 1:
        raise ValueError("times 必须大于等于 1")

    def decorate(target: Callable) -> Callable:
        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait = delay
            for attempt in range(1, times + 1):
                try:
                    return target(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= times:
                        raise
                    if logger is not None:
                        logger.warning(
                            "%s 第 %d 次失败：%s", target.__qualname__, attempt, exc
                        )
                    if wait > 0:
                        time.sleep(wait)
                    wait *= backoff
            raise RuntimeError(f"{target.__qualname__} 重试逻辑异常")

        return wrapper

    return decorate


def memoize(func: Callable) -> Callable:
    """按调用参数缓存返回值，参数需可哈希；不可哈希时退化为直接调用。"""

    def decorate(target: Callable) -> Callable:
        cache: dict[Any, Any] = {}

        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                key = (args, tuple(sorted(kwargs.items())))
                if key not in cache:
                    cache[key] = target(*args, **kwargs)
            except TypeError:
                return target(*args, **kwargs)
            return cache[key]

        wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
        return wrapper

    return decorate(func)


def silent(
    default: Any = None,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable:
    """吞掉指定异常并返回默认值。"""

    def decorate(target: Callable) -> Callable:
        @functools.wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return target(*args, **kwargs)
            except exceptions:
                return default

        return wrapper

    return decorate


def singleton[T](cls: type[T]) -> type[T]:
    """让类只保留一个实例，重复实例化返回同一对象；__init__ 仍会重复执行。"""
    instances: dict[type, Any] = {}
    original_new = cls.__new__

    def new(sub_cls: type, *args: Any, **kwargs: Any) -> Any:
        if sub_cls not in instances:
            instances[sub_cls] = original_new(sub_cls)
        return instances[sub_cls]

    cls.__new__ = staticmethod(new)  # type: ignore[assignment]
    return cls
