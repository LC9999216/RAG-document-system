import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.errors import register_exception_handlers


class ErrorHandlersTest(unittest.TestCase):
    def test_http_exception_uses_consistent_error_shape(self):
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/boom")
        async def boom():
            raise HTTPException(status_code=400, detail="坏请求")

        client = TestClient(app)
        response = client.get("/boom")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "http_error",
                    "message": "坏请求",
                },
            },
        )

    def test_unhandled_exception_returns_internal_error_shape(self):
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/crash")
        async def crash():
            raise RuntimeError("unexpected")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/crash")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "internal_error",
                    "message": "服务器内部错误，请稍后重试。",
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
