"""PySide6 集成（需 fdy[gui]）。

五块能力互相独立，可以只用其中一块：

- `Chain`：链式配置 Qt 控件，不往 Qt 类型上打补丁
- `on` / `bind`：声明式信号槽绑定
- `Column` / `TableModel`：Python 数据 → Qt 表格模型
- `dialogs`：信息 / 警告 / 错误 / 确认 / 文本输入的一行式封装
- `Settings`：QSettings 的类型化读写与窗口几何持久化

`dialogs` 里的函数不重导出到包级 —— `fdy.gui.error` 这种名字与日志语义撞车，
调用方写 `dialogs.confirm(...)` 更清楚。
"""

from ..core._optional import require

require("PySide6")

# 可选依赖必须先校验，故子模块的导入不能提到文件顶部
from . import chain, dialogs, models, settings, signals  # noqa: E402
from .chain import Chain  # noqa: E402
from .models import Column, TableModel  # noqa: E402
from .settings import Settings  # noqa: E402
from .signals import Binding, bind, on, unbind  # noqa: E402

__all__ = [
    "Binding",
    "Chain",
    "Column",
    "Settings",
    "TableModel",
    "bind",
    "chain",
    "dialogs",
    "models",
    "on",
    "settings",
    "signals",
    "unbind",
]
