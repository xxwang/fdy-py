"""Column / TableModel 的行为测试。"""

from dataclasses import dataclass

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt

from fdy.gui import Column, TableModel


@dataclass
class Person:
    name: str
    balance: int


@dataclass(frozen=True)
class Frozen:
    name: str


class Plain:
    def __init__(self, name: str) -> None:
        self.name = name


COLUMNS = [Column("name", "姓名"), Column("balance", "余额", editable=True)]


@pytest.fixture
def model(qapp):
    return TableModel([Person("张三", 100), Person("李四", 200)], COLUMNS)


def test_shape(model):
    assert model.rowCount() == 2
    assert model.columnCount() == 2


def test_child_parent_has_no_rows(model):
    parent = model.index(0, 0)

    assert model.rowCount(parent) == 0
    assert model.columnCount(parent) == 0


def test_display_role_from_dataclass(model):
    assert model.data(model.index(0, 0)) == "张三"
    assert model.data(model.index(1, 1)) == "200"


def test_display_role_from_dict(qapp):
    m = TableModel([{"name": "王五", "balance": 300}], COLUMNS)

    assert m.data(m.index(0, 0)) == "王五"


def test_display_role_from_plain_object(qapp):
    m = TableModel([Plain("赵六")], [Column("name")])

    assert m.data(m.index(0, 0)) == "赵六"


def test_nested_key(qapp):
    m = TableModel([{"user": {"name": "张三"}}], [Column("user.name")])

    assert m.data(m.index(0, 0)) == "张三"


def test_missing_key_renders_empty(qapp):
    m = TableModel([{"name": "张三"}], [Column("missing")])

    assert m.data(m.index(0, 0)) == ""


def test_formatter_overrides_text(qapp):
    m = TableModel(
        [Person("张三", 12345)],
        [Column("balance", formatter=lambda value: f"¥{value:,}")],
    )

    assert m.data(m.index(0, 0)) == "¥12,345"


def test_edit_role_returns_raw_text(model):
    assert model.data(model.index(1, 1), Qt.ItemDataRole.EditRole) == "200"


def test_alignment_role(qapp):
    m = TableModel(
        [Person("张三", 1)], [Column("balance", align=Qt.AlignmentFlag.AlignRight)]
    )

    assert (
        m.data(m.index(0, 0), Qt.ItemDataRole.TextAlignmentRole)
        == Qt.AlignmentFlag.AlignRight
    )


def test_unhandled_role_returns_none(model):
    assert model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole) is None


def test_invalid_index_returns_none(model):
    assert model.data(QModelIndex()) is None


def test_header_data(model):
    assert model.headerData(0, Qt.Orientation.Horizontal) == "姓名"
    assert model.headerData(1, Qt.Orientation.Horizontal) == "余额"
    assert model.headerData(0, Qt.Orientation.Vertical) == 1
    assert (
        model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole)
        is None
    )


def test_header_falls_back_to_key(qapp):
    m = TableModel([], [Column("name")])

    assert m.headerData(0, Qt.Orientation.Horizontal) == "name"


def test_flags_track_editable(model):
    assert model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable
    assert not model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable


def test_flags_on_invalid_index_are_selectable_only(model):
    expected = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    assert model.flags(QModelIndex()) == expected


def test_set_data_writes_editable_column(model):
    assert model.setData(model.index(0, 1), 999) is True
    assert model.row_at(0).balance == 999


def test_set_data_announces_change(model):
    seen: list[int] = []
    model.dataChanged.connect(lambda *_: seen.append(1))

    model.setData(model.index(0, 1), 999)

    assert seen == [1]


def test_set_data_rejects_readonly_column(model):
    assert model.setData(model.index(0, 0), "改不动") is False
    assert model.row_at(0).name == "张三"


def test_set_data_rejects_non_edit_role(model):
    assert model.setData(model.index(0, 1), 999, Qt.ItemDataRole.DisplayRole) is False


def test_set_data_on_frozen_dataclass_returns_false(qapp):
    m = TableModel([Frozen("张三")], [Column("name", editable=True)])

    assert m.setData(m.index(0, 0), "李四") is False
    assert m.row_at(0).name == "张三"


def test_set_data_writes_through_nested_dict(qapp):
    data = [{"user": {"name": "张三"}}]
    m = TableModel(data, [Column("user.name", editable=True)])

    assert m.setData(m.index(0, 0), "李四") is True
    assert data[0]["user"]["name"] == "李四"


def test_set_data_on_invalid_index(model):
    assert model.setData(QModelIndex(), 1) is False


def test_append_row_announces_range(model):
    spans: list[tuple[int, int]] = []
    model.rowsInserted.connect(lambda *args: spans.append(args[1:]))

    model.append_row(Person("王五", 300))

    assert spans == [(2, 2)]
    assert model.rowCount() == 3
    assert model.row_at(2).name == "王五"


def test_insert_row_announces_range(model):
    spans: list[tuple[int, int]] = []
    model.rowsInserted.connect(lambda *args: spans.append(args[1:]))

    model.insert_row(0, Person("王五", 300))

    assert spans == [(0, 0)]
    assert model.row_at(0).name == "王五"


def test_remove_row_announces_range_and_returns_row(model):
    spans: list[tuple[int, int]] = []
    model.rowsRemoved.connect(lambda *args: spans.append(args[1:]))

    removed = model.remove_row(0)

    assert spans == [(0, 0)]
    assert removed.name == "张三"
    assert model.rowCount() == 1


def test_update_row_announces_change(model):
    seen: list[int] = []
    model.dataChanged.connect(lambda *_: seen.append(1))

    model.update_row(1, Person("李四", 999))

    assert seen == [1]
    assert model.row_at(1).balance == 999


def test_set_rows_resets_model(model):
    resets: list[int] = []
    model.modelReset.connect(lambda: resets.append(1))

    model.set_rows([Person("王五", 300)])

    assert resets == [1]
    assert model.rowCount() == 1


def test_clear_empties_model(model):
    model.clear()

    assert model.rowCount() == 0


def test_rows_returns_a_copy(model):
    snapshot = model.rows()
    snapshot.append(Person("王五", 300))

    assert model.rowCount() == 2


def test_columns_are_exposed_read_only(model):
    assert model.columns == tuple(COLUMNS)


def test_update_row_without_columns_is_safe(qapp):
    m = TableModel([Person("张三", 1)], [])

    m.update_row(0, Person("李四", 2))

    assert m.rowCount() == 1
