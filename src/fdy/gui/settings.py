"""QSettings 的薄封装。

```
settings = Settings(QSettings("RichesMe", "FinNet"))
window.resize(settings.value("main/width", 1024), settings.value("main/height", 768))
settings.save_geometry("main/window", window)
```

只补两件 QSettings 本身没做好的事：读取时按默认值的类型规范化返回值，
以及窗口几何的存取往返。
"""

from typing import Any

from PySide6.QtCore import QByteArray, QSettings
from PySide6.QtWidgets import QWidget

__all__ = [
    "Settings",
]

_TRUTHY = frozenset({"1", "true", "yes", "on"})


class Settings:
    """按 key 读写配置，读时用默认值兜底并决定返回类型。"""

    def __init__(self, store: QSettings) -> None:
        self._store = store

    @property
    def store(self) -> QSettings:
        """底层 QSettings，用于 group / 数组等本封装未覆盖的用法。"""
        return self._store

    def value[T](self, key: str, default: T) -> T:
        """读 key；缺失返回 default，存在则规范化到 default 的类型。

        `default` 同时是类型声明，所以不要传 `None` 之外的占位值来「只要原始值」。
        """
        raw = self._store.value(key)
        return default if raw is None else _coerce(raw, default)

    def set(self, key: str, value: object) -> None:
        self._store.setValue(key, value)

    def remove(self, key: str) -> None:
        self._store.remove(key)

    def clear(self) -> None:
        self._store.clear()

    def sync(self) -> None:
        """立即落盘（QSettings 默认延迟写入）。"""
        self._store.sync()

    def save_geometry(self, key: str, widget: QWidget) -> None:
        """保存窗口的位置与尺寸。"""
        self._store.setValue(key, widget.saveGeometry())

    def restore_geometry(self, key: str, widget: QWidget) -> bool:
        """恢复窗口几何；无记录或数据不是几何值时返回 False 且不动窗口。

        返回 True 也不代表尺寸与保存时一致：Qt 会把超出屏幕可用区域的几何
        收进去（换显示器 / 分辨率变小后，防止窗口落到看不见的地方），
        实测 800x800 屏幕上存 1440x900 会恢复成 798x774。
        """
        blob = self._store.value(key)
        if not isinstance(blob, QByteArray):
            return False
        return widget.restoreGeometry(blob)


def _coerce[T](raw: Any, default: T) -> T:
    """把回读值规范到 default 的类型。

    某些后端会把值读成字符串，此时 `bool("false") is True` 会让开关读反，
    所以 bool 必须单独按字面量判定，不能走 `bool(...)`。
    """
    if isinstance(default, bool):
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in _TRUTHY
    if isinstance(default, (int, float, str)):
        return type(default)(raw)
    return raw
