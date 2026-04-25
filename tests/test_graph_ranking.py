import unittest
from unittest.mock import Mock

from langchain_core.documents import Document

from app.graphs.graph import RAGGraph


class GraphRankingTest(unittest.TestCase):
    def test_retrieve_node_reranks_irrelevant_matches(self):
        vector_store = Mock()
        vector_store.is_empty.return_value = False
        vector_store.similarity_search.return_value = [
            (
                Document(
                    page_content="《机械原理》重点考点",
                    metadata={"source": "机械原理.pdf", "page": 0},
                ),
                0.98,
            ),
            (
                Document(
                    page_content="# 测试文档\n\n## 结论\n\n这是结论部分。",
                    metadata={"source": "test.md", "page": 1},
                ),
                1.15,
            ),
        ]

        graph = RAGGraph(vector_store)

        state = graph._retrieve_node({"question": "结论是什么？", "matches": [], "documents": [], "answer": ""})

        self.assertEqual(state["matches"][0][0].metadata["source"], "test.md")
        self.assertEqual(state["documents"][0].metadata["source"], "test.md")

    def test_retrieve_node_expands_chinese_query_synonyms(self):
        vector_store = Mock()
        vector_store.is_empty.return_value = False
        vector_store.similarity_search.return_value = [
            (
                Document(
                    page_content="机械原理重点考点，主要覆盖齿轮、连杆和凸轮机构。",
                    metadata={"source": "机械原理.pdf", "page": 0},
                ),
                0.92,
            ),
            (
                Document(
                    page_content="# 2035全球科技格局预测\n\n商业机会：AI基础设施、机器人、新能源、自动化软件将是未来十年的核心赛道。",
                    metadata={"source": "未来科技预测.md", "page": 1},
                ),
                1.08,
            ),
        ]

        graph = RAGGraph(vector_store)

        state = graph._retrieve_node({"question": "未来可以哪些方面会有重大机遇", "matches": [], "documents": [], "answer": ""})

        self.assertEqual(state["matches"][0][0].metadata["source"], "未来科技预测.md")
        self.assertEqual(state["documents"][0].metadata["source"], "未来科技预测.md")


if __name__ == "__main__":
    unittest.main()
