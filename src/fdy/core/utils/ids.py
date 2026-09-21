"""标识符与令牌生成。"""

import secrets
import uuid
from typing import Any

__all__ = [
    "is_valid_uuid",
    "short_id",
    "token_hex",
    "token_urlsafe",
    "uuid_str",
]

# 剔除 0/O/1/l/I 等易混淆字符，便于人工转录
_SAFE_ALPHABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"


def uuid_str() -> str:
    """生成标准 UUID4 字符串。"""
    return str(uuid.uuid4())


def short_id(length: int = 10, alphabet: str | None = None) -> str:
    """生成短随机 ID，默认字母表已排除易混淆字符。"""
    if length <= 0:
        raise ValueError("length 必须大于 0")
    chars = alphabet if alphabet else _SAFE_ALPHABET
    return "".join(secrets.choice(chars) for _ in range(length))


def token_hex(nbytes: int = 16) -> str:
    """生成十六进制随机令牌，长度为 nbytes 的两倍。"""
    return secrets.token_hex(nbytes)


def token_urlsafe(nbytes: int = 16) -> str:
    """生成 URL 安全的随机令牌。"""
    return secrets.token_urlsafe(nbytes)


def is_valid_uuid(value: Any, version: int | None = None) -> bool:
    """校验 UUID 字符串，可指定版本号（如 4）。"""
    try:
        parsed = uuid.UUID(str(value))
    except ValueError, AttributeError, TypeError:
        return False
    return version is None or parsed.version == version
