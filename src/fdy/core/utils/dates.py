"""日期时间工具，默认以带时区的 UTC 为基准。"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

__all__ = [
    "date_range",
    "days_between",
    "end_of_day",
    "format_datetime",
    "from_timestamp",
    "humanize_delta",
    "now",
    "parse_datetime",
    "start_of_day",
    "start_of_month",
    "to_timestamp",
]

_FALLBACK_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%Y-%m-%d",
    "%Y%m%d",
)

_HUMAN_UNITS = (
    (365 * 86400, "年"),
    (30 * 86400, "个月"),
    (86400, "天"),
    (3600, "小时"),
    (60, "分钟"),
    (1, "秒"),
)


def now(tz: timezone | None = None) -> datetime:
    """当前时间，默认返回带时区的 UTC 时间。"""
    return datetime.now(tz or UTC)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def parse_datetime(value: Any, default: datetime | None = None) -> datetime | None:
    """解析日期时间，支持 datetime/date 对象与常见字符串格式，失败返回 default。"""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if not isinstance(value, str):
        return default
    text = value.strip()
    if not text:
        return default
    try:
        return _ensure_utc(datetime.fromisoformat(text))
    except ValueError:
        pass
    for fmt in _FALLBACK_FORMATS:
        try:
            return _ensure_utc(datetime.strptime(text, fmt))
        except ValueError:
            continue
    return default


def format_datetime(
    value: Any, fmt: str = "%Y-%m-%d %H:%M:%S", default: str = ""
) -> str:
    """按 fmt 格式化日期时间，无法解析时返回 default。"""
    parsed = parse_datetime(value)
    return default if parsed is None else parsed.strftime(fmt)


def to_timestamp(value: Any, default: float = 0.0) -> float:
    """转为 Unix 时间戳（秒），无时区的输入按 UTC 解释。"""
    parsed = parse_datetime(value)
    if parsed is None:
        return default
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.timestamp()


def from_timestamp(timestamp: float, tz: timezone | None = None) -> datetime:
    """从 Unix 时间戳（秒）还原为 datetime。"""
    return datetime.fromtimestamp(timestamp, tz or UTC)


def humanize_delta(value: Any, default: str = "") -> str:
    """把时间差、秒数或时间点描述为「3 分钟前 / 2 天后」这样的相对时间。"""
    if isinstance(value, timedelta):
        delta = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        delta = timedelta(seconds=value)
    else:
        target = parse_datetime(value)
        if target is None:
            return default
        if target.tzinfo is None:
            target = target.replace(tzinfo=UTC)
        delta = now() - target

    seconds = delta.total_seconds()
    suffix = "后" if seconds < 0 else "前"
    seconds = abs(seconds)
    if seconds < 60:
        return "刚刚" if seconds < 10 else f"{int(seconds)} 秒{suffix}"
    for unit_seconds, label in _HUMAN_UNITS:
        if seconds >= unit_seconds:
            return f"{int(seconds // unit_seconds)} {label}{suffix}"
    return f"{int(seconds)} 秒{suffix}"


def days_between(start: Any, end: Any) -> int:
    """计算两个日期相差的天数（end - start），无法解析时抛 ValueError。"""
    first, second = _as_date(start), _as_date(end)
    if first is None or second is None:
        raise ValueError("无法解析日期")
    return (second - first).days


def date_range(start: Any, end: Any, step_days: int = 1) -> Iterator[date]:
    """生成闭区间 [start, end] 的日期序列，含首尾两端。"""
    if step_days <= 0:
        raise ValueError("step_days 必须大于 0")
    current, last = _as_date(start), _as_date(end)
    if current is None or last is None:
        raise ValueError("无法解析日期")
    if current > last:
        raise ValueError("start 不能晚于 end")
    while current <= last:
        yield current
        current += timedelta(days=step_days)


def start_of_day(value: Any = None) -> datetime:
    """取当天 00:00:00，保留原时区信息。"""
    return _require(value).replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(value: Any = None) -> datetime:
    """取当天 23:59:59.999999。"""
    return _require(value).replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_month(value: Any = None) -> datetime:
    """取当月 1 日 00:00:00。"""
    return start_of_day(value).replace(day=1)


def _require(value: Any) -> datetime:
    moment = now() if value is None else parse_datetime(value)
    if moment is None:
        raise ValueError(f"无法解析日期：{value!r}")
    return moment


def _as_date(value: Any) -> date | None:
    parsed = parse_datetime(value)
    return None if parsed is None else parsed.date()
