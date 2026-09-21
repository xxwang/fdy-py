"""声明式信号槽绑定。

`@on` 只做标记、不产生副作用，真正建立连接的是 `bind(obj)`；
连接时机由调用方掌握，便于在 `__init__` 末尾统一接线，也便于测试里手工控制：

    class Dialog(QDialog):
        def __init__(self) -> None:
            super().__init__()
            self.btn_ok = QPushButton("确定")
            bind(self)

        @on("clicked")  # 发送者是被 bind 的实例自身
        def _on_dialog_clicked(self) -> None: ...

        @on("clicked", sender="btn_ok")  # 发送者从实例属性上取
        def _confirm(self) -> None: ...
"""

import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject

__all__ = [
    "Binding",
    "bind",
    "on",
    "unbind",
]

_MARK = "__fdy_signal_bindings__"


@dataclass(frozen=True, slots=True)
class Binding:
    """一条 `@on` 声明。"""

    signal: str
    sender: str | None = None


def on[F: Callable[..., Any]](
    signal: str,
    *,
    sender: str | None = None,
) -> Callable[[F], F]:
    """把方法登记为 `signal` 的槽。

    Args:
        signal: 信号名，如 `"clicked"`。
        sender: 发送者所在的实例属性名；省略时发送者是 `bind()` 传入的对象自身。
    """

    def decorator(func: F) -> F:
        declared = (*getattr(func, _MARK, ()), Binding(signal=signal, sender=sender))
        setattr(func, _MARK, declared)
        return func

    return decorator


def bind(obj: QObject) -> int:
    """连接 `obj` 的类上所有被 `@on` 标记的方法，返回建立的连接数。

    按 MRO 顺序扫描，子类覆盖父类同名方法时以子类为准（父类的声明不会重复连接）。
    """
    count = 0
    for name, binding in _declared(type(obj)):
        slot = getattr(obj, name)
        signal = _signal_of(obj, binding)
        signal.connect(slot)
        count += 1
    return count


def unbind(obj: QObject) -> None:
    """断开 `bind(obj)` 建立的连接；重复调用是安全的。"""
    for name, binding in _declared(type(obj)):
        slot = getattr(obj, name)
        try:
            with warnings.catch_warnings():
                # 未连接时 libpyside 只发 RuntimeWarning、不抛异常（实测 6.11），
                # 压掉它才能让 unbind 保持幂等且不污染调用方日志。
                # catch_warnings 会改进程级过滤器，故 unbind 只应在主线程调用。
                warnings.simplefilter("ignore")
                _signal_of(obj, binding).disconnect(slot)
        except RuntimeError:  # 其他 PySide6 版本可能改为抛异常
            continue


def _signal_of(obj: Any, binding: Binding) -> Any:
    sender = obj if binding.sender is None else _require(obj, binding.sender, "sender")
    signal = _require(sender, binding.signal, "signal")
    if not hasattr(signal, "connect"):
        raise AttributeError(
            f"{type(sender).__name__} 上的 {binding.signal!r} 不是信号"
        )
    return signal


def _require(obj: Any, name: str, kind: str) -> Any:
    value = getattr(obj, name, None)
    if value is None:
        raise AttributeError(f"{type(obj).__name__} 上没有 {kind} {name!r}")
    return value


def _declared(cls: type) -> Iterator[tuple[str, Binding]]:
    """按 MRO 顺序收集 `@on` 声明，同名方法只取最靠近子类的那个。"""
    seen: set[str] = set()
    for klass in cls.__mro__:
        for name, member in vars(klass).items():
            if name in seen:
                continue
            seen.add(name)
            for binding in getattr(member, _MARK, ()):
                yield name, binding
