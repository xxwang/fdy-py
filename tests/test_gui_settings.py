"""Settings 的行为测试。"""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from fdy.gui import Settings


@pytest.fixture
def ini_path(tmp_path):
    return str(tmp_path / "settings.ini")


@pytest.fixture
def settings(ini_path):
    return Settings(QSettings(ini_path, QSettings.Format.IniFormat))


def test_value_round_trips_stored_value(settings):
    settings.set("name", "fdy")

    assert settings.value("name", "") == "fdy"


def test_value_returns_default_when_absent(settings):
    assert settings.value("nope", "fallback") == "fallback"
    assert settings.value("nope", 7) == 7


def test_bool_default_normalises_string_values(settings):
    # 模拟把 bool 存成字符串的后端（注册表 / 手改过的 ini）：
    # 直接 bool("false") 会得到 True，开关就被读反了
    settings.set("flag", "false")
    assert settings.value("flag", True) is False

    settings.set("flag", "True")
    assert settings.value("flag", True) is True


def test_bool_default_keeps_real_bool(settings):
    settings.set("flag", False)

    assert settings.value("flag", True) is False


def test_int_and_float_defaults_coerce_strings(settings):
    settings.set("count", "42")
    settings.set("ratio", "1.5")

    assert settings.value("count", 0) == 42
    assert settings.value("ratio", 0.0) == 1.5


def test_str_default_coerces_numbers(settings):
    settings.set("port", 8080)

    assert settings.value("port", "") == "8080"


def test_untyped_default_passes_raw_through(settings):
    settings.set("key", "value")

    assert settings.value("key", None) == "value"
    assert settings.value("absent", None) is None


def test_store_exposes_underlying_qsettings(settings):
    settings.store.beginGroup("db")
    settings.store.setValue("host", "localhost")
    settings.store.endGroup()

    assert settings.value("db/host", "") == "localhost"


def test_remove_and_clear(settings):
    settings.set("a", 1)
    settings.set("b", 2)
    settings.remove("a")
    assert settings.value("a", -1) == -1

    settings.clear()
    assert settings.value("b", -1) == -1


def test_sync_writes_through_to_disk(settings, ini_path):
    settings.set("key", "value")
    settings.sync()

    reopened = Settings(QSettings(ini_path, QSettings.Format.IniFormat))

    assert reopened.value("key", "") == "value"


def test_geometry_round_trip(qapp, settings):
    source = QWidget()
    source.resize(320, 200)
    settings.save_geometry("win", source)

    restored = QWidget()

    assert settings.restore_geometry("win", restored) is True
    assert (restored.width(), restored.height()) == (320, 200)


def test_restore_geometry_returns_false_when_absent(qapp, settings):
    widget = QWidget()

    assert settings.restore_geometry("win", widget) is False


def test_restore_geometry_keeps_window_within_screen(qapp, settings):
    # 返回 True 不等于尺寸完全一致：Qt 会把超屏几何收进屏幕可用区域
    screen = QGuiApplication.primaryScreen().availableGeometry()
    source = QWidget()
    source.resize(screen.width() * 2, screen.height() * 2)
    settings.save_geometry("win", source)

    restored = QWidget()

    assert settings.restore_geometry("win", restored) is True
    assert restored.width() <= screen.width()
    assert restored.height() <= screen.height()


def test_restore_geometry_rejects_corrupt_data(qapp, settings):
    widget = QWidget()
    widget.resize(300, 100)
    settings.set("win", "not a geometry blob")

    assert settings.restore_geometry("win", widget) is False
    assert (widget.width(), widget.height()) == (300, 100)
