"""Chain 链式封装的行为测试。"""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel, QPushButton

from fdy.gui import Chain


def test_done_returns_wrapped_object(qapp):
    button = QPushButton("确定")

    assert Chain(button).done() is button


def test_every_setter_returns_self(qapp):
    wrapper = Chain(QPushButton("x"))

    assert wrapper.set(text="y") is wrapper
    assert wrapper.text("z") is wrapper
    assert wrapper.enabled() is wrapper
    assert wrapper.visible() is wrapper
    assert wrapper.tooltip("t") is wrapper
    assert wrapper.resize(10, 10) is wrapper
    assert wrapper.style("color: red") is wrapper


def test_set_applies_multiple_properties(qapp):
    button = (
        Chain(QPushButton("确定"))
        .set(text="保存", enabled=False, visible=False, checkable=True)
        .done()
    )

    assert button.text() == "保存"
    assert button.isEnabled() is False
    assert button.isVisible() is False
    assert button.isCheckable() is True


def test_set_accepts_snake_case(qapp):
    button = (
        Chain(QPushButton("x")).set(object_name="btn_save", tool_tip="Ctrl+S").done()
    )

    assert button.objectName() == "btn_save"
    assert button.toolTip() == "Ctrl+S"


def test_set_accepts_qml_style_camel_case(qapp):
    button = Chain(QPushButton("x")).set(toolTip="Ctrl+S").done()

    assert button.toolTip() == "Ctrl+S"


def test_set_accepts_trailing_underscore(qapp):
    assert Chain(QPushButton("x")).set(text_="确定").done().text() == "确定"


def test_unknown_property_reports_case_variant(qapp):
    # Qt 属性名大小写敏感：setTooltip 不存在，真名是 setToolTip
    with pytest.raises(AttributeError, match=r"没有可设置的属性 'tooltip'.*'tool_tip'"):
        Chain(QPushButton("x")).set(tooltip="Ctrl+S")


def test_unknown_property_without_variant_has_no_hint(qapp):
    with pytest.raises(AttributeError) as excinfo:
        Chain(QPushButton("x")).set(not_a_property=1)

    assert "是否想写" not in str(excinfo.value)


def test_convenience_method_on_non_widget_raises(qapp):
    with pytest.raises(AttributeError, match="QObject 上没有方法 setStyleSheet"):
        Chain(QObject()).style("color: red")


def test_connect_wires_signal(qapp):
    button = QPushButton("确定")
    hits: list[int] = []

    Chain(button).connect("clicked", lambda: hits.append(1))
    button.click()

    assert hits == [1]


def test_connect_unknown_signal_raises(qapp):
    with pytest.raises(AttributeError, match="没有信号 'no_such_signal'"):
        Chain(QPushButton("x")).connect("no_such_signal", lambda: None)


def test_target_is_readable_and_repr_names_class(qapp):
    button = QPushButton("x")
    wrapper = Chain(button)

    assert wrapper.target is button
    assert repr(wrapper) == "Chain(QPushButton)"


def test_works_on_non_button_widget(qapp):
    label = Chain(QLabel()).set(text="加载中").style("font-size: 12px;").done()

    assert label.text() == "加载中"
    assert label.styleSheet() == "font-size: 12px;"
