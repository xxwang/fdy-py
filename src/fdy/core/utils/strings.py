"""字符串处理工具。"""

import re
import secrets
import string as _string

__all__ = [
    "camel_case",
    "kebab_case",
    "mask",
    "normalize_space",
    "pascal_case",
    "random_string",
    "slugify",
    "snake_case",
    "truncate",
]

_WORD_SEPARATOR = re.compile(r"[-_\s]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_NON_WORD = re.compile(r"[^A-Za-z0-9]+")


def _split_words(text: str) -> list[str]:
    words: list[str] = []
    for part in _WORD_SEPARATOR.split(text.strip()):
        if part:
            words.extend(word for word in _CAMEL_BOUNDARY.split(part) if word)
    return words


def snake_case(text: str) -> str:
    """转换为 snake_case，支持驼峰、短横线与空格输入。"""
    return "_".join(word.lower() for word in _split_words(text))


def kebab_case(text: str) -> str:
    """转换为 kebab-case。"""
    return "-".join(word.lower() for word in _split_words(text))


def camel_case(text: str) -> str:
    """转换为小驼峰 camelCase。"""
    words = _split_words(text)
    if not words:
        return ""
    head, *tail = words
    return head.lower() + "".join(word.capitalize() for word in tail)


def pascal_case(text: str) -> str:
    """转换为大驼峰 PascalCase。"""
    return "".join(word.capitalize() for word in _split_words(text))


def slugify(text: str) -> str:
    """转换为 URL 友好的 slug，非字母数字字符折叠为单个短横线。"""
    return _NON_WORD.sub("-", text.strip().lower()).strip("-")


def truncate(text: str, length: int = 50, suffix: str = "...") -> str:
    """截断到指定长度，超长时保留前段并追加 suffix。"""
    if length < 0:
        raise ValueError("length 不能为负数")
    if len(text) <= length:
        return text
    if len(suffix) >= length:
        return suffix[:length]
    return text[: length - len(suffix)] + suffix


def mask(value: str, keep_start: int = 0, keep_end: int = 0, char: str = "*") -> str:
    """脱敏保留首尾若干字符，如 mask("13812345678", 3, 4) -> "138****5678"。"""
    if keep_start < 0 or keep_end < 0:
        raise ValueError("keep_start/keep_end 不能为负数")
    if keep_start + keep_end >= len(value):
        return value
    hidden = len(value) - keep_start - keep_end
    return value[:keep_start] + char * hidden + value[len(value) - keep_end :]


def random_string(length: int = 16, alphabet: str | None = None) -> str:
    """生成随机字符串，默认字母数字组合，使用 secrets 保证密码学安全。"""
    if length <= 0:
        raise ValueError("length 必须大于 0")
    chars = _string.ascii_letters + _string.digits if alphabet is None else alphabet
    if not chars:
        raise ValueError("alphabet 不能为空")
    return "".join(secrets.choice(chars) for _ in range(length))


def normalize_space(text: str) -> str:
    """把连续空白折叠为单个空格并去除首尾空白。"""
    return re.sub(r"\s+", " ", text).strip()
