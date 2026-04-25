import unittest

from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings

from app.storage.vector_store import VectorStoreManager
from tests._tempdir import managed_tempdir


class VectorStoreManagerTest(unittest.TestCase):
    def test_delete_documents_by_reference_rebuilds_index(self):
        with managed_tempdir() as temp_dir:
            manager = VectorStoreManager(
                embeddings=FakeEmbeddings(size=8),
                persist_path=temp_dir,
            )

            manager.add_documents(
                [
                    Document(page_content="alpha", metadata={"doc_id": "doc_1", "source": "a.md", "page": 1}),
                    Document(page_content="beta", metadata={"doc_id": "doc_2", "source": "b.md", "page": 1}),
                ]
            )

            removed = manager.delete_documents_by_reference("doc_1", source="a.md")

            self.assertEqual(removed, 1)
            self.assertEqual(manager.get_document_count(), 1)


if __name__ == "__main__":
    unittest.main()
