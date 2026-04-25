import unittest

from app.storage.storage import StorageManager
from tests._tempdir import managed_tempdir


class StorageManagerTest(unittest.TestCase):
    def test_add_document_preserves_generated_or_supplied_id(self):
        with managed_tempdir() as temp_dir:
            manager = StorageManager(persist_path=temp_dir)

            generated = manager.add_document("generated.md", 2)
            supplied = manager.add_document("supplied.md", 3, doc_id="doc_custom")

            self.assertTrue(generated["id"].startswith("doc_"))
            self.assertEqual(supplied["id"], "doc_custom")

            documents = manager.get_documents()
            self.assertEqual(len(documents), 2)
            self.assertEqual(documents[0]["file_name"], "generated.md")
            self.assertEqual(documents[1]["file_name"], "supplied.md")


if __name__ == "__main__":
    unittest.main()
