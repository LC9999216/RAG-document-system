import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.storage.storage import StorageManager


def _load_json_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Legacy JSON file must contain a list: {path}")


def _archive_legacy_file(path: Path, backup_dir: Path) -> bool:
    if not path.exists():
        return False

    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / path.name
    if target.exists():
        return False

    shutil.move(str(path), str(target))
    return True


def migrate_legacy_json_files(persist_path: str = "./vector_store") -> dict:
    base_path = Path(persist_path)
    storage = StorageManager(str(base_path))
    backup_dir = base_path / "legacy_backup"

    documents_path = base_path / "documents.json"
    chat_history_path = base_path / "chat_history.json"

    documents = _load_json_file(documents_path)
    chat_messages = _load_json_file(chat_history_path)

    documents_imported = storage.import_documents(documents)
    chat_messages_imported = storage.import_chat_messages(chat_messages)
    archived_files = 0
    archived_files += int(_archive_legacy_file(documents_path, backup_dir))
    archived_files += int(_archive_legacy_file(chat_history_path, backup_dir))

    return {
        "persist_path": str(base_path),
        "documents_found": len(documents),
        "documents_imported": documents_imported,
        "chat_messages_found": len(chat_messages),
        "chat_messages_imported": chat_messages_imported,
        "archived_files": archived_files,
        "legacy_backup_path": str(backup_dir),
        "db_path": storage.db_path,
    }


if __name__ == "__main__":
    result = migrate_legacy_json_files()
    print(json.dumps(result, ensure_ascii=False, indent=2))
