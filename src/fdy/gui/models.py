"""把 Python 数据适配成 Qt 表格模型。

手写 `QAbstractTableModel` 的样板代码（rowCount / columnCount / data / headerData /
flags / setData + 一整套 begin/end 信号配对）在每个项目里都要重来一遍，
这里用「列描述 + 通用取值」把它收敛掉：

    columns = [
        Column("name", "姓名"),
        Column("balance", "余额", align=Qt.AlignmentFlag.AlignRight),
        Column("note", "备注", editable=True),
    ]
    view.setModel(TableModel(rows, columns))

行可以是 dict、dataclass、pydantic 模型或普通对象；
`key` 支持点号路径（`"user.name"`），按 Mapping 索引与属性访问依次尝试。
"""

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

__all__ = [
    "Column",
    "TableModel",
]

_ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_SELECTABLE = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


@dataclass(frozen=True, slots=True)
class Column:
    """一列的描述：取值键、表头标题与可选格式化。"""

    key: str
    title: str = ""
    editable: bool = False
    align: Qt.AlignmentFlag = _ALIGN_LEFT
    formatter: Callable[[Any], str] | None = None

    def text(self, row: Any) -> str:
        """取出该列的值并转成显示文本；None 显示为空串。"""
        value = _extract(row, self.key)
        if self.formatter is not None:
            return self.formatter(value)
        return "" if value is None else str(value)


class TableModel[T](QAbstractTableModel):
    """把一组行数据适配成 Qt 表格模型。"""

    def __init__(
        self,
        rows: Sequence[T],
        columns: Sequence[Column],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._rows: list[T] = list(rows)
        self._columns: tuple[Column, ...] = tuple(columns)

    @property
    def columns(self) -> tuple[Column, ...]:
        """当前列定义（只读）。"""
        return self._columns

    def rows(self) -> list[T]:
        """当前数据的浅拷贝。"""
        return list(self._rows)

    def row_at(self, row: int) -> T:
        """按下标取原始行对象。"""
        return self._rows[row]

    def set_rows(self, rows: Sequence[T]) -> None:
        """整体替换数据。"""
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def append_row(self, row: T) -> None:
        """在末尾追加一行。"""
        self.insert_row(len(self._rows), row)

    def insert_row(self, row: int, data: T) -> None:
        """在下标 `row` 处插入一行。"""
        self.beginInsertRows(QModelIndex(), row, row)
        self._rows.insert(row, data)
        self.endInsertRows()

    def update_row(self, row: int, data: T) -> None:
        """替换某一行并刷新该行的所有列。"""
        self._rows[row] = data
        last = max(len(self._columns) - 1, 0)
        self.dataChanged.emit(self.index(row, 0), self.index(row, last))

    def remove_row(self, row: int) -> T:
        """删除某一行，返回被删掉的对象。"""
        self.beginRemoveRows(QModelIndex(), row, row)
        removed = self._rows.pop(row)
        self.endRemoveRows()
        return removed

    def clear(self) -> None:
        """清空所有数据。"""
        self.set_rows([])

    @override
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    @override
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columns)

    @override
    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        column = self._columns[index.column()]
        row = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return column.text(row)
        if role == Qt.ItemDataRole.EditRole:
            value = _extract(row, column.key)
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return column.align
        return None

    @override
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            column = self._columns[section]
            # 没给标题时退化成字段名，比空白表头有信息量
            return column.title or column.key
        return section + 1

    @override
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if index.isValid() and self._columns[index.column()].editable:
            return _SELECTABLE | Qt.ItemFlag.ItemIsEditable
        return _SELECTABLE

    @override
    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        column = self._columns[index.column()]
        if not column.editable:
            return False
        if not _assign(self._rows[index.row()], column.key, value):
            return False
        self.dataChanged.emit(index, index)
        return True


def _extract(row: Any, key: str) -> Any:
    """按 `a.b.c` 路径取值，每层依次尝试 Mapping 索引与属性访问。"""
    current = row
    for part in key.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _assign(row: Any, key: str, value: Any) -> bool:
    """按 `a.b.c` 路径写入，写入点不可变时返回 False。"""
    head, _, leaf = key.rpartition(".")
    target = _extract(row, head) if head else row
    if target is None:
        return False
    if isinstance(target, MutableMapping):
        target[leaf] = value
        return True
    try:
        setattr(target, leaf, value)
    except AttributeError:
        # dataclass(frozen=True)、只读 property 等会走到这里
        return False
    return True
