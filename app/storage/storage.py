import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, TypedDict


class DocumentInfo(TypedDict):
    id: str
    file_name: str
    upload_time: str
    chunks: int


class DocumentChunkInfo(TypedDict):
    chunk_id: str
    doc_id: str
    source: str
    page: int
    created_at: str


class ChatMessage(TypedDict):
    id: str
    role: str
    content: str
    citations: List[dict]
    timestamp: str


class StorageManager:
    def __init__(self, persist_path: str = "./vector_store"):
        self.persist_path = persist_path
        os.makedirs(persist_path, exist_ok=True)
        self.db_path = os.path.join(persist_path, "app.db")
        self._initialize_database()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    upload_time TEXT NOT NULL,
                    chunks INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    page INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                """
            )

    def generate_document_id(self) -> str:
        with self._connect() as connection:
            document_count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        return f"doc_{document_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def add_document(self, file_name: str, chunks: int, doc_id: str | None = None) -> DocumentInfo:
        doc_id = doc_id or self.generate_document_id()
        upload_time = datetime.now().isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, file_name, upload_time, chunks, status)
                VALUES (?, ?, ?, ?, 'active')
                """,
                (doc_id, file_name, upload_time, chunks),
            )
        return DocumentInfo(
            id=doc_id,
            file_name=file_name,
            upload_time=upload_time,
            chunks=chunks,
        )

    def import_documents(self, documents: List[DocumentInfo]) -> int:
        if not documents:
            return 0

        rows = [
            (
                document["id"],
                document["file_name"],
                document["upload_time"],
                int(document["chunks"]),
            )
            for document in documents
        ]
        with self._connect() as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO documents (id, file_name, upload_time, chunks, status)
                VALUES (?, ?, ?, ?, 'active')
                """,
                rows,
            )
            return connection.total_changes - before

    def add_document_chunks(self, doc_id: str, chunks: List[dict]) -> None:
        if not chunks:
            return

        created_at = datetime.now().isoformat()
        rows = [
            (doc_id, chunk["chunk_id"], chunk["source"], int(chunk.get("page", 0)), created_at)
            for chunk in chunks
        ]
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO document_chunks (doc_id, chunk_id, source, page, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

    def get_documents(self) -> List[DocumentInfo]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, file_name, upload_time, chunks
                FROM documents
                WHERE status = 'active'
                ORDER BY upload_time ASC
                """
            ).fetchall()
        return [DocumentInfo(**dict(row)) for row in rows]

    def get_document(self, doc_id: str) -> DocumentInfo | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, file_name, upload_time, chunks
                FROM documents
                WHERE id = ? AND status = 'active'
                """,
                (doc_id,),
            ).fetchone()
        return DocumentInfo(**dict(row)) if row else None

    def get_document_chunks(self, doc_id: str) -> List[DocumentChunkInfo]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunk_id, doc_id, source, page, created_at
                FROM document_chunks
                WHERE doc_id = ?
                ORDER BY id ASC
                """,
                (doc_id,),
            ).fetchall()
        return [DocumentChunkInfo(**dict(row)) for row in rows]

    def delete_document(self, doc_id: str) -> bool:
        with self._connect() as connection:
            result = connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return result.rowcount > 0

    def add_message(self, role: str, content: str, citations: List[dict] = None) -> ChatMessage:
        citations = citations or []
        timestamp = datetime.now().isoformat()
        with self._connect() as connection:
            message_count = connection.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
            msg_id = f"msg_{message_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            connection.execute(
                """
                INSERT INTO chat_messages (id, role, content, citations_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (msg_id, role, content, json.dumps(citations, ensure_ascii=False), timestamp),
            )
        return ChatMessage(
            id=msg_id,
            role=role,
            content=content,
            citations=citations,
            timestamp=timestamp,
        )

    def import_chat_messages(self, messages: List[ChatMessage]) -> int:
        if not messages:
            return 0

        rows = [
            (
                message["id"],
                message["role"],
                message["content"],
                json.dumps(message.get("citations", []), ensure_ascii=False),
                message["timestamp"],
            )
            for message in messages
        ]
        with self._connect() as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO chat_messages (id, role, content, citations_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
            return connection.total_changes - before

    def get_chat_history(self, limit: int = 50) -> List[ChatMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, citations_json, timestamp
                FROM chat_messages
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return list(reversed([self._to_chat_message(row) for row in rows]))

    def get_all_chat_history(self) -> List[ChatMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, citations_json, timestamp
                FROM chat_messages
                ORDER BY timestamp ASC
                """
            ).fetchall()
        return [self._to_chat_message(row) for row in rows]

    def clear_chat_history(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chat_messages")

    def search_documents(self, query: str) -> List[DocumentInfo]:
        query_like = f"%{query.lower()}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, file_name, upload_time, chunks
                FROM documents
                WHERE status = 'active' AND LOWER(file_name) LIKE ?
                ORDER BY upload_time ASC
                """,
                (query_like,),
            ).fetchall()
        return [DocumentInfo(**dict(row)) for row in rows]

    def _to_chat_message(self, row: sqlite3.Row) -> ChatMessage:
        citations = json.loads(row["citations_json"]) if row["citations_json"] else []
        return ChatMessage(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            citations=citations,
            timestamp=row["timestamp"],
        )
