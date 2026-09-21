"""fdy.web 异常处理器的行为契约（需 fdy[web]）。"""

import asyncio
import json

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

from fdy.core.exceptions.api_exception import APIException
from fdy.web import api_exception_handler, register_exception_handlers


@pytest.fixture
def app():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise APIException(code=1001, message="余额不足", status_code=400)

    @app.get("/gone")
    async def gone():
        raise APIException(code=1002, message="资源不存在", status_code=404)

    @app.get("/ok")
    async def ok():
        return {"fine": True}

    @app.get("/crash")
    async def crash():
        raise ValueError("非 APIException")

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_registers_handler_for_api_exception(app):
    assert app.exception_handlers[APIException] is api_exception_handler


def test_api_exception_becomes_unified_payload(client):
    response = client.get("/boom")

    assert response.status_code == 400
    assert response.json() == {"code": 1001, "message": "余额不足", "data": None}


def test_custom_status_code_is_honoured(client):
    response = client.get("/gone")

    assert response.status_code == 404
    assert response.json()["code"] == 1002


def test_normal_route_is_untouched(client):
    response = client.get("/ok")

    assert response.status_code == 200
    assert response.json() == {"fine": True}


def test_other_exceptions_are_not_intercepted(app):
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/crash")

    assert response.status_code == 500
    assert "code" not in response.text


def test_handler_is_usable_without_fastapi_routing():
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

    response = asyncio.run(
        api_exception_handler(
            request, APIException(code=7, message="独立调用", status_code=422)
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 422
    assert json.loads(response.body) == {
        "code": 7,
        "message": "独立调用",
        "data": None,
    }


def test_web_stays_out_of_top_level_namespace():
    import fdy

    assert "web" not in fdy.__all__
