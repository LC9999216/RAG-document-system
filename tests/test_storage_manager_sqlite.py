import unittest
from pathlib import Path

from app.storage.storage import StorageManager
from tests._tempdir import managed_tempdir


class StorageManagerSQLiteTest(unittest.TestCase):
    def test_initialization_creates_sqlite_database_file(self):
        with managed_tempdir() as temp_dir:
            manager = StorageManager(persist_path=temp_dir)

            self.assertTrue(Path(manager.db_path).exists())

    def test_document_chunk_mappings_are_persisted(self):
        with managed_tempdir() as temp_dir:
            manager = StorageManager(persist_path=temp_dir)
            doc = manager.add_document("sample.md", 2, doc_id="doc_1")

            manager.add_document_chunks(
                doc["id"],
                [
                    {"chunk_id": "doc_1_chunk_0", "source": "sample.md", "page": 1},
                    {"chunk_id": "doc_1_chunk_1", "source": "sample.md", "page": 2},
                ],
            )

            chunks = manager.get_document_chunks(doc["id"])
            self.assertEqual(len(chunks), 2)
            self.assertEqual(chunks[0]["chunk_id"], "doc_1_chunk_0")
            self.assertEqual(chunks[1]["page"], 2)

    def test_chat_messages_are_persisted_in_sqlite(self):
        with managed_tempdir() as temp_dir:
            manager = StorageManager(persist_path=temp_dir)

            manager.add_message("user", "hello")
            manager.add_message(
                "assistant",
                "world",
                citations=[{"source": "sample.md", "page": 1, "score": 1.0, "text": "snippet"}],
            )

            history = manager.get_all_chat_history()
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["role"], "user")
            self.assertEqual(history[1]["citations"][0]["source"], "sample.md")


if __name__ == "__main__":
    unittest.main()
