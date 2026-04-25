import json
import unittest
from pathlib import Path

from app.storage.storage import StorageManager
from scripts.migrate_json_to_sqlite import migrate_legacy_json_to_sqlite
from tests._tempdir import managed_tempdir


class JsonToSqliteMigrationTest(unittest.TestCase):
    def test_migrates_legacy_json_files_into_sqlite(self):
        with managed_tempdir() as temp_dir:
            persist_path = Path(temp_dir)
            (persist_path / "documents.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "doc_1",
                            "file_name": "legacy.md",
                            "upload_time": "2026-04-24T10:00:00",
                            "chunks": 2,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (persist_path / "chat_history.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "msg_1",
                            "role": "user",
                            "content": "hello",
                            "citations": [],
                            "timestamp": "2026-04-24T10:01:00",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = migrate_legacy_json_to_sqlite(str(persist_path))
            manager = StorageManager(str(persist_path))

            self.assertEqual(result["documents_imported"], 1)
            self.assertEqual(result["chat_messages_imported"], 1)
            self.assertEqual(len(manager.get_documents()), 1)
            self.assertEqual(len(manager.get_all_chat_history()), 1)
            self.assertTrue((persist_path / "legacy_backup" / "documents.json").exists())
            self.assertTrue((persist_path / "legacy_backup" / "chat_history.json").exists())

    def test_migration_is_idempotent(self):
        with managed_tempdir() as temp_dir:
            persist_path = Path(temp_dir)
            payload = [
                {
                    "id": "doc_1",
                    "file_name": "legacy.md",
                    "upload_time": "2026-04-24T10:00:00",
                    "chunks": 2,
                }
            ]
            (persist_path / "documents.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            first = migrate_legacy_json_to_sqlite(str(persist_path))

            backup_file = persist_path / "legacy_backup" / "documents.json"
            (persist_path / "documents.json").write_text(backup_file.read_text(encoding="utf-8"), encoding="utf-8")
            second = migrate_legacy_json_to_sqlite(str(persist_path))
            manager = StorageManager(str(persist_path))

            self.assertEqual(first["documents_imported"], 1)
            self.assertEqual(second["documents_imported"], 0)
            self.assertEqual(len(manager.get_documents()), 1)


if __name__ == "__main__":
    unittest.main()
