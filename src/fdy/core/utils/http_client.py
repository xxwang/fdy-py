"""基于 httpx 的轻量 HTTP 客户端。

httpx 属于可选依赖：未安装时不影响 `import fdy`，只在真正发起请求时抛出带安装提示的 ImportError。
"""

from typing import Any

from .._optional import require

__all__ = [
    "HttpClient",
    "get_json",
    "post_json",
]

_RETRYABLE_STATUS = 500


class HttpClient:
    """带默认超时、统一请求头与失败重试的 HTTP 客户端。"""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
        retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"User-Agent": "fdy/0.1", **(headers or {})}
        self.retries = max(retries, 0)

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """发起请求，网络错误与 5xx 响应自动重试，其余状态码由 raise_for_status 抛出。"""
        httpx = require("httpx")
        target = f"{self.base_url}{url}" if self.base_url else url
        options: dict[str, Any] = {
            "timeout": self.timeout,
            "headers": self.headers,
            **kwargs,
        }
        attempts = self.retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = httpx.request(method, target, **options)
            except httpx.TransportError:
                if attempt >= attempts:
                    raise
                continue
            if response.status_code >= _RETRYABLE_STATUS and attempt < attempts:
                continue
            response.raise_for_status()
            return response
        raise RuntimeError(f"请求失败：{target}")

    def get(self, url: str, **kwargs: Any) -> Any:
        """发起 GET 请求。"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        """发起 POST 请求。"""
        return self.request("POST", url, **kwargs)

    def get_json(self, url: str, **kwargs: Any) -> Any:
        """发起 GET 请求并解析响应 JSON。"""
        return self.get(url, **kwargs).json()

    def post_json(self, url: str, payload: Any = None, **kwargs: Any) -> Any:
        """以 JSON 体发起 POST 请求并解析响应 JSON。"""
        return self.post(url, json=payload, **kwargs).json()


def get_json(url: str, timeout: float = 10.0, **kwargs: Any) -> Any:
    """一次性 GET 请求并解析 JSON。"""
    return HttpClient(timeout=timeout).get_json(url, **kwargs)


def post_json(
    url: str, payload: Any = None, timeout: float = 10.0, **kwargs: Any
) -> Any:
    """一次性 POST JSON 请求并解析响应 JSON。"""
    return HttpClient(timeout=timeout).post_json(url, payload, **kwargs)
