"""可选依赖加载器 require() 的行为契约。"""

import sys

import pytest

from fdy.core._optional import require


def test_require_returns_module_object():
    json = require("json")

    assert json.dumps({"a": 1}) == '{"a": 1}'


def test_missing_module_maps_to_extra_command(monkeypatch):
    monkeypatch.setitem(sys.modules, "httpx", None)

    with pytest.raises(ImportError, match=r'pip install "fdy\[http\]"'):
        require("httpx")


def test_unmapped_module_falls_back_to_bare_install(monkeypatch):
    monkeypatch.setitem(sys.modules, "some_random_pkg", None)

    with pytest.raises(ImportError, match=r"pip install some_random_pkg$"):
        require("some_random_pkg")


def test_original_error_is_chained(monkeypatch):
    monkeypatch.setitem(sys.modules, "httpx", None)

    with pytest.raises(ImportError) as excinfo:
        require("httpx")

    assert isinstance(excinfo.value.__cause__, ImportError)
