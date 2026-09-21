"""dialogs 的行为测试。"""

import sys

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget

from fdy.gui import dialogs

# Qt 在 macOS 上按 Apple HIG 忽略消息框标题：QMessageBox::setWindowTitle 的
# Q_OS_MAC 分支是 Q_UNUSED(title) 空操作，标题既进不了 windowTitle() 也到不了
# 平台窗口。这条差异写成断言固定住，免得日后误判成自己的 bug。
_TITLE_HONOURED = sys.platform != "darwin"


def _patch_exec(monkeypatch, cls, code, sink, on_call=None):
    """替换对话框的 exec：不弹窗，返回预设值，并把对话框收进 sink。"""

    def _exec(self):
        if on_call is not None:
            on_call(self)
        sink.append(self)
        return code

    monkeypatch.setattr(cls, "exec", _exec)


class _FakeApp:
    """替掉 dialogs 模块里的 QApplication，让 activeWindow 可控。"""

    window = None

    @classmethod
    def activeWindow(cls):  # noqa: N802 —— 有意镜像 Qt 的 API 名，非本项目命名风格
        return cls.window


def test_info_fills_message_and_icon(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.info("已保存", title="完成")

    box = boxes[0]
    assert box.text() == "已保存"
    assert box.icon() == QMessageBox.Icon.Information


def test_message_box_title_follows_platform_rules(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.info("x", title="完成")
    dialogs.warn("x", title="警告标题")

    expected = ["完成", "警告标题"] if _TITLE_HONOURED else ["", ""]
    assert [box.windowTitle() for box in boxes] == expected


def test_warn_and_error_pick_matching_icons(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.warn("注意")
    dialogs.error("炸了")

    assert [box.icon() for box in boxes] == [
        QMessageBox.Icon.Warning,
        QMessageBox.Icon.Critical,
    ]


def test_confirm_is_true_only_for_ok(qapp, monkeypatch):
    boxes = []
    # 真实的 exec() 返回 int，这里用 int 而不是枚举，锁住两者的相等语义
    _patch_exec(monkeypatch, QMessageBox, int(QMessageBox.StandardButton.Ok), boxes)
    assert dialogs.confirm("继续？") is True

    _patch_exec(monkeypatch, QMessageBox, int(QMessageBox.StandardButton.Cancel), boxes)
    assert dialogs.confirm("继续？") is False


def test_confirm_treats_closed_dialog_as_false(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    assert dialogs.confirm("继续？") is False


def test_confirm_button_texts_are_overridable(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.confirm("保存？", ok_text="保存", cancel_text="再想想")

    box = boxes[0]
    assert box.button(QMessageBox.StandardButton.Ok).text() == "保存"
    assert box.button(QMessageBox.StandardButton.Cancel).text() == "再想想"


def test_destructive_confirm_defaults_to_cancel(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.confirm("删除？", destructive=True)
    dialogs.confirm("删除？")

    assert boxes[0].defaultButton().text() == "取消"
    assert boxes[1].defaultButton().text() == "确定"


def test_parent_defaults_to_active_window(qapp, monkeypatch):
    window = QWidget()
    monkeypatch.setattr(dialogs, "QApplication", _FakeApp)
    monkeypatch.setattr(_FakeApp, "window", window)
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.info("hi")

    assert boxes[0].parent() is window


def test_explicit_parent_wins_over_active_window(qapp, monkeypatch):
    parent = QWidget()
    monkeypatch.setattr(dialogs, "QApplication", _FakeApp)
    monkeypatch.setattr(_FakeApp, "window", QWidget())
    boxes = []
    _patch_exec(monkeypatch, QMessageBox, 0, boxes)

    dialogs.info("hi", parent=parent)

    assert boxes[0].parent() is parent


def test_ask_text_returns_typed_value(qapp, monkeypatch):
    boxes = []

    def type_into(box):
        box.setTextValue("用户输入")

    _patch_exec(monkeypatch, QInputDialog, 1, boxes, on_call=type_into)

    assert dialogs.ask_text("名称？", title="新建", default="默认") == "用户输入"


def test_ask_text_returns_none_on_cancel(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QInputDialog, 0, boxes)

    assert dialogs.ask_text("名称？") is None


def test_ask_text_passes_label_and_default(qapp, monkeypatch):
    boxes = []
    _patch_exec(monkeypatch, QInputDialog, 0, boxes)

    dialogs.ask_text("名称？", title="新建", default="默认值")

    box = boxes[0]
    assert box.labelText() == "名称？"
    assert box.windowTitle() == "新建"
    assert box.textValue() == "默认值"
