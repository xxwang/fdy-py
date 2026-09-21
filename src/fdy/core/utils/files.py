"""文件与路径工具。"""

import hashlib
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

__all__ = [
    "ensure_dir",
    "file_hash",
    "human_size",
    "iter_files",
    "read_json",
    "read_text",
    "safe_filename",
    "unique_path",
    "write_json",
    "write_text",
]

_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")
_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def human_size(size: int | float, precision: int = 2) -> str:
    """字节数转为可读大小，如 1536 -> "1.5 KB"。"""
    if size < 0:
        raise ValueError("size 不能为负数")
    value = float(size)
    index = 0
    while value >= 1024 and index < len(_SIZE_UNITS) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return f"{int(value)} B"
    text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    return f"{text} {_SIZE_UNITS[index]}"


def ensure_dir(path: str | os.PathLike) -> Path:
    """创建目录（含所有父级），已存在时不报错。"""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def read_text(
    path: str | os.PathLike, encoding: str = "utf-8", default: str | None = None
) -> str | None:
    """读取文本文件，文件不存在或解码失败时返回 default。"""
    try:
        return Path(path).read_text(encoding=encoding)
    except OSError, UnicodeDecodeError:
        return default


def write_text(
    path: str | os.PathLike,
    content: str,
    encoding: str = "utf-8",
    make_parents: bool = True,
) -> Path:
    """写入文本，默认自动创建父目录。"""
    target = Path(path)
    if make_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding=encoding)
    return target


def read_json(
    path: str | os.PathLike, default: Any = None, encoding: str = "utf-8"
) -> Any:
    """读取 JSON 文件，文件缺失或内容非法时返回 default。"""
    raw = read_text(path, encoding=encoding)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def write_json(
    path: str | os.PathLike,
    data: Any,
    indent: int | None = 2,
    ensure_ascii: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """写入 JSON 文件，默认保留中文且不转义。"""
    payload = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    return write_text(path, payload, encoding=encoding)


def iter_files(
    root: str | os.PathLike = ".", pattern: str = "*", recursive: bool = True
) -> Iterator[Path]:
    """遍历目录下的文件，可按 glob 模式过滤，只产出文件不产出目录。"""
    base = Path(root)
    if not base.is_dir():
        return
    candidates = base.rglob(pattern) if recursive else base.glob(pattern)
    for item in candidates:
        if item.is_file():
            yield item


def safe_filename(name: str, replacement: str = "_") -> str:
    """过滤文件名中的非法字符，并去掉首尾空白与点号。"""
    cleaned = _ILLEGAL_FILENAME_CHARS.sub(replacement, name).strip().rstrip(".")
    return cleaned or "untitled"


def unique_path(path: str | os.PathLike, max_attempts: int = 1000) -> Path:
    """路径已存在时追加 (1)、(2) 等序号，返回第一个可用的路径。"""
    target = Path(path)
    if not target.exists():
        return target
    for index in range(1, max_attempts + 1):
        candidate = target.parent / f"{target.stem} ({index}){target.suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"在 {max_attempts} 次尝试后仍未找到可用路径：{target}")


def file_hash(
    path: str | os.PathLike,
    algorithm: str = "sha256",
    chunk_size: int = 65536,
    default: str | None = None,
) -> str | None:
    """计算文件摘要，默认 sha256，分块读取以支持大文件。文件不可读时返回 default。"""
    try:
        digest = hashlib.new(algorithm)
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(chunk_size), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return default
