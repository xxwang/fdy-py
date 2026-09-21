"""Qt 控件的链式配置。

不往 Qt 类型上打补丁（`QPushButton.setText = ...` 那种写法会污染全局命名空间，
且随 Qt 版本升级容易冲突），而是用轻量包装器 `Chain` 包住目标对象，
配完再用 `done()` 取回原对象：

    from fdy.gui import Chain

    button = (
        Chain(QPushButton("确定"))
        .set(text="保存", object_name="btn_save")
        .tooltip("Ctrl+S")
        .resize(120, 32)
        .style("font-weight: 600;")
        .connect("clicked", on_save)
        .done()
    )

`set()` 的属性名按 Qt 原名大小写敏感（`toolTip` 而非 `tooltip`），
所以同时接受 snake_case 写法：`tool_tip` 与 `toolTip` 都能解析到 `setToolTip`。

入口只有 `Chain` 类、没有同名函数，是刻意的：模块名与函数名撞车时，
`fdy.gui.chain` 究竟指向模块还是函数取决于导入方式，是纯粹的自找麻烦。
"""

from collections.abc import Callable
from typing import Any, Self

from PySide6.QtCore import QObject

from ..core.utils.strings import snake_case

__all__ = [
    "Chain",
]


class Chain[T: QObject]:
    """链式配置包装器：每个 setter 返回自身，`done()` 取回原对象。"""

    def __init__(self, target: T) -> None:
        self._target = target

    def __repr__(self) -> str:
        return f"Chain({type(self._target).__name__})"

    @property
    def target(self) -> T:
        """被包装的对象（只读）。"""
        return self._target

    def set(self, **properties: Any) -> Self:
        """按 Qt 属性名批量赋值。

        属性名支持 snake_case（`object_name` → `setObjectName`）、
        camelCase（`objectName`）与尾随下划线（`text_`）三种写法；
        目标对象上没有对应 setter 时抛 `AttributeError`；若只是大小写差异
        （写了 `tooltip` 而 Qt 真名是 `toolTip`），报错里直接给出 `tool_tip`。
        """
        for name, value in properties.items():
            setter_name = _setter_name(name)
            setter = getattr(self._target, setter_name, None)
            if not callable(setter):
                hint = _case_mismatch(self._target, setter_name)
                raise AttributeError(
                    f"{type(self._target).__name__} 上没有可设置的属性 {name!r}"
                    f"{f'，是否想写 {hint!r}？' if hint else ''}"
                )
            setter(value)
        return self

    def connect(self, signal: str, slot: Callable[..., Any]) -> Self:
        """连接信号。"""
        source = getattr(self._target, signal, None)
        if source is None or not hasattr(source, "connect"):
            raise AttributeError(f"{type(self._target).__name__} 上没有信号 {signal!r}")
        source.connect(slot)
        return self

    def text(self, value: str) -> Self:
        return self._call("setText", value)

    def enabled(self, value: bool = True) -> Self:
        return self._call("setEnabled", value)

    def visible(self, value: bool = True) -> Self:
        return self._call("setVisible", value)

    def tooltip(self, value: str) -> Self:
        return self._call("setToolTip", value)

    def resize(self, width: int, height: int) -> Self:
        return self._call("resize", width, height)

    def style(self, sheet: str) -> Self:
        """设置样式表。"""
        return self._call("setStyleSheet", sheet)

    def done(self) -> T:
        """取回被包装的对象，结束链式调用。"""
        return self._target

    def _call(self, method: str, *args: Any) -> Self:
        func = getattr(self._target, method, None)
        if not callable(func):
            raise AttributeError(f"{type(self._target).__name__} 上没有方法 {method}")
        func(*args)
        return self


def _setter_name(property_name: str) -> str:
    """属性名 → setter 名：`text` / `object_name` / `objectName` → `setObjectName` 等。"""
    head, *rest = property_name.rstrip("_").split("_")
    suffix = "".join(part[:1].upper() + part[1:] for part in rest)
    return f"set{head[:1].upper()}{head[1:]}{suffix}"


def _case_mismatch(target: QObject, setter_name: str) -> str | None:
    """找出只差大小写的同名 setter，返回其 snake_case 属性名。

    Qt 属性名大小写敏感：`tooltip` 会解析成 `setTooltip`，真名却是 `setToolTip` ——
    这类错误最难自查，所以报错时直接给出正确写法。只做大小写比对、不做模糊匹配，
    模糊匹配会把 `not_a_property` 提示成 `property`，那是误导。
    """
    lowered = setter_name.lower()
    for name in dir(target):
        if len(name) > 3 and name.startswith("set") and name.lower() == lowered:
            return snake_case(name[3:])
    return None
