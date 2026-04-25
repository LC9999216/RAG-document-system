import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api import routes


class RoutesServiceInitTest(unittest.TestCase):
    def test_get_rag_service_returns_503_when_service_init_fails(self):
        routes._rag_service = None
        routes._rag_service_error = None

        with patch("app.api.routes.RAGService", side_effect=RuntimeError("init failed")):
            with self.assertRaises(HTTPException) as context:
                routes.get_rag_service()

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "RAG 服务暂时不可用，请检查模型和向量库配置。")


if __name__ == "__main__":
    unittest.main()
