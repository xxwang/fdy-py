"""常用对话框的一行式封装。

```
if dialogs.confirm("删除后不可恢复，确定吗？", destructive=True):
    delete()
```

未显式传 `parent` 时会挂到当前活动窗口上，避免对话框脱离主窗口跑到屏幕角落。

关于 `title`：Qt 在 macOS 上按 Apple HIG 忽略消息框标题
（`QMessageBox::setWindowTitle` 的 `Q_OS_MAC` 分支是空操作），
所以 `info` / `warn` / `error` / `confirm` 的 `title` 只在 Windows / Linux 生效。
`ask_text` 走的是 QInputDialog，没有这个限制。
"""

from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox, QWidget

__all__ = [
    "ask_text",
    "confirm",
    "error",
    "info",
    "warn",
]


def info(message: str, *, title: str = "提示", parent: QWidget | None = None) -> None:
    """信息提示框。"""
    _box(QMessageBox.Icon.Information, message, title, parent).exec()


def warn(message: str, *, title: str = "警告", parent: QWidget | None = None) -> None:
    """警告提示框。"""
    _box(QMessageBox.Icon.Warning, message, title, parent).exec()


def error(message: str, *, title: str = "错误", parent: QWidget | None = None) -> None:
    """错误提示框。"""
    _box(QMessageBox.Icon.Critical, message, title, parent).exec()


def confirm(
    message: str,
    *,
    title: str = "确认",
    parent: QWidget | None = None,
    ok_text: str = "确定",
    cancel_text: str = "取消",
    destructive: bool = False,
) -> bool:
    """确认框，确定返回 True。

    `destructive=True` 用于删除这类不可逆操作：默认按钮落在「取消」上，
    避免用户顺手按回车就把数据删了。
    """
    box = _box(QMessageBox.Icon.Question, message, title, parent)
    box.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
    )
    ok = box.button(QMessageBox.StandardButton.Ok)
    cancel = box.button(QMessageBox.StandardButton.Cancel)
    ok.setText(ok_text)
    cancel.setText(cancel_text)
    box.setDefaultButton(cancel if destructive else ok)
    return box.exec() == QMessageBox.StandardButton.Ok


def ask_text(
    message: str,
    *,
    title: str = "输入",
    default: str = "",
    parent: QWidget | None = None,
) -> str | None:
    """单行文本输入，取消返回 None。

    None 与空字符串含义不同：前者是「放弃输入」，后者是「确定输入了空内容」。
    """
    box = QInputDialog(_parent(parent))
    box.setWindowTitle(title)
    box.setLabelText(message)
    box.setTextValue(default)
    return box.textValue() if box.exec() else None


def _box(
    icon: QMessageBox.Icon,
    message: str,
    title: str,
    parent: QWidget | None,
) -> QMessageBox:
    box = QMessageBox(_parent(parent))
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(message)
    return box


def _parent(parent: QWidget | None) -> QWidget | None:
    return parent if parent is not None else QApplication.activeWindow()
