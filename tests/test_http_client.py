import sys

import httpx
import pytest

from fdy import http_client


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = {} if payload is None else payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_get_json_parses_response(monkeypatch):
    monkeypatch.setattr(
        httpx, "request", lambda method, url, **kwargs: _FakeResponse(200, {"ok": True})
    )
    assert http_client.get_json("https://example.com/api") == {"ok": True}


def test_post_json_sends_payload(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen["method"] = method
        seen["json"] = kwargs.get("json")
        return _FakeResponse(200, {"created": True})

    monkeypatch.setattr(httpx, "request", fake_request)
    assert http_client.post_json("https://example.com/items", {"name": "fdy"}) == {
        "created": True
    }
    assert seen == {"method": "POST", "json": {"name": "fdy"}}


def test_base_url_is_joined_with_path(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen["url"] = url
        return _FakeResponse(200, {})

    monkeypatch.setattr(httpx, "request", fake_request)
    http_client.HttpClient("https://api.example.com/").get("/ping")
    assert seen["url"] == "https://api.example.com/ping"


def test_default_user_agent_is_sent(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen["headers"] = kwargs.get("headers")
        return _FakeResponse(200, {})

    monkeypatch.setattr(httpx, "request", fake_request)
    http_client.HttpClient().get("https://example.com")
    assert seen["headers"]["User-Agent"] == "fdy/0.1"


def test_custom_headers_override_defaults(monkeypatch):
    seen = {}

    def fake_request(method, url, **kwargs):
        seen["headers"] = kwargs.get("headers")
        return _FakeResponse(200, {})

    monkeypatch.setattr(httpx, "request", fake_request)
    http_client.HttpClient(headers={"User-Agent": "custom/2.0"}).get(
        "https://example.com"
    )
    assert seen["headers"]["User-Agent"] == "custom/2.0"


def test_retries_on_server_error(monkeypatch):
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        calls["n"] += 1
        return _FakeResponse(500 if calls["n"] == 1 else 200, {"ok": True})

    monkeypatch.setattr(httpx, "request", fake_request)
    assert http_client.HttpClient(retries=1).get_json("https://example.com") == {
        "ok": True
    }
    assert calls["n"] == 2


def test_retries_on_transport_error(monkeypatch):
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("连接失败")
        return _FakeResponse(200, {})

    monkeypatch.setattr(httpx, "request", fake_request)
    http_client.HttpClient(retries=1).get("https://example.com")
    assert calls["n"] == 2


def test_raises_when_retries_exhausted(monkeypatch):
    def fake_request(method, url, **kwargs):
        raise httpx.ConnectError("连接失败")

    monkeypatch.setattr(httpx, "request", fake_request)
    with pytest.raises(httpx.ConnectError):
        http_client.HttpClient(retries=1).get("https://example.com")


def test_client_error_is_not_retried(monkeypatch):
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        calls["n"] += 1
        return _FakeResponse(404)

    monkeypatch.setattr(httpx, "request", fake_request)
    with pytest.raises(RuntimeError, match="404"):
        http_client.HttpClient(retries=2).get("https://example.com/missing")
    assert calls["n"] == 1


def test_negative_retries_are_clamped(monkeypatch):
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        calls["n"] += 1
        return _FakeResponse(200, {})

    monkeypatch.setattr(httpx, "request", fake_request)
    assert http_client.HttpClient(retries=-5).retries == 0
    http_client.HttpClient(retries=-5).get("https://example.com")
    assert calls["n"] == 1


def test_missing_httpx_gives_install_hint(monkeypatch):
    # sys.modules 里塞 None 是模拟「模块存在但不可导入」的可靠手法；
    # 靠 monkeypatch builtins.__import__ 拦不住 importlib.import_module。
    monkeypatch.setitem(sys.modules, "httpx", None)

    with pytest.raises(ImportError, match=r'pip install "fdy\[http\]"'):
        http_client.HttpClient().get("https://example.com")
