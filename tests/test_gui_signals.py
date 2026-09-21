"""@on / bind / unbind 的行为测试。"""

from dataclasses import FrozenInstanceError

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPushButton

from fdy.gui import Binding, bind, on, unbind


class Counter(QObject):
    """信号挂在被 bind 的对象自身。"""

    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.hits = 0

    @on("clicked")
    def _on_clicked(self) -> None:
        self.hits += 1


class Panel(QObject):
    """信号挂在子控件上，用 sender 指定。"""

    def __init__(self) -> None:
        super().__init__()
        self.btn_ok = QPushButton("确定")
        self.hits = 0

    @on("clicked", sender="btn_ok")
    def _on_ok(self) -> None:
        self.hits += 1


class Multi(QObject):
    first = Signal()
    second = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    @on("first")
    @on("second")
    def _ping(self) -> None:
        self.count += 1


class Base(QObject):
    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    @on("clicked")
    def _handle(self) -> None:
        self.tags.append("base")


class Child(Base):
    pass


class Overriding(Base):
    @on("clicked")
    def _handle(self) -> None:
        self.tags.append("child")


def test_bind_connects_declared_slot(qapp):
    counter = Counter()

    assert bind(counter) == 1
    counter.clicked.emit()

    assert counter.hits == 1


def test_without_bind_nothing_is_connected(qapp):
    counter = Counter()
    counter.clicked.emit()

    assert counter.hits == 0


def test_bind_without_declarations_returns_zero(qapp):
    assert bind(QObject()) == 0


def test_sender_attribute_resolves_child_signal(qapp):
    panel = Panel()

    assert bind(panel) == 1
    panel.btn_ok.click()

    assert panel.hits == 1


def test_inherited_declaration_is_connected(qapp):
    child = Child()
    bind(child)
    child.clicked.emit()

    assert child.tags == ["base"]


def test_override_replaces_declaration_without_duplicate(qapp):
    obj = Overriding()

    assert bind(obj) == 1
    obj.clicked.emit()

    # 父类声明若也被连上，这里会变成 ["child", "child"]
    assert obj.tags == ["child"]


def test_one_method_can_listen_to_multiple_signals(qapp):
    obj = Multi()

    assert bind(obj) == 2
    obj.first.emit()
    obj.second.emit()

    assert obj.count == 2


def test_unbind_disconnects(qapp):
    counter = Counter()
    bind(counter)
    unbind(counter)
    counter.clicked.emit()

    assert counter.hits == 0


def test_unbind_without_bind_is_ignored(qapp):
    unbind(Counter())  # 不应抛异常


def test_unknown_signal_raises(qapp):
    class Bad(QObject):
        @on("no_such_signal")
        def _go(self) -> None: ...

    with pytest.raises(AttributeError, match="没有 signal 'no_such_signal'"):
        bind(Bad())


def test_unknown_sender_raises(qapp):
    class Bad(QObject):
        clicked = Signal()

        @on("clicked", sender="missing")
        def _go(self) -> None: ...

    with pytest.raises(AttributeError, match="没有 sender 'missing'"):
        bind(Bad())


def test_declaring_a_plain_method_raises(qapp):
    class Bad(QObject):
        def not_a_signal(self) -> None: ...

        @on("not_a_signal")
        def _go(self) -> None: ...

    with pytest.raises(AttributeError, match="不是信号"):
        bind(Bad())


def test_binding_is_frozen():
    binding = Binding(signal="clicked", sender="btn_ok")

    assert binding.sender == "btn_ok"
    with pytest.raises(FrozenInstanceError):
        binding.signal = "other"
