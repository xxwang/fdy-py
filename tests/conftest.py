"""测试级公共配置。"""

import os

import pytest

# Qt 需要无头平台插件才能在没有显示器的环境（CI、沙箱）里初始化，
# 且必须在 PySide6 被导入之前设置，故放在 conftest 的模块级别。
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """会话级 QApplication：Qt 只允许进程内存在一个实例，不能按用例重建。"""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])
