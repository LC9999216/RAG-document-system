import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.embeddings import get_embedding_model


MetadataFilter = Callable[[Document], bool]


class VectorStoreManager:
    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        persist_path: Optional[str] = None
    ):
        self.embeddings = embeddings or get_embedding_model()
        self.persist_path = persist_path or os.getenv("VECTOR_STORE_PATH", "./vector_store")
        self.index_file = os.path.join(self.persist_path, os.getenv("INDEX_FILE", "index.faiss"))
        self.metadata_file = os.path.join(self.persist_path, os.getenv("METADATA_FILE", "index.pkl"))
        self.index_name = Path(self.index_file).stem
        self.vector_store: Optional[FAISS] = None
        self._load()

    def _load(self) -> bool:
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            try:
                self.vector_store = FAISS.load_local(
                    self.persist_path,
                    self.embeddings,
                    index_name=self.index_name,
                    allow_dangerous_deserialization=True
                )
                return True
            except Exception:
                return False
        return False

    def save(self) -> None:
        if self.vector_store is not None:
            os.makedirs(self.persist_path, exist_ok=True)
            self.vector_store.save_local(self.persist_path, index_name=self.index_name)

    def add_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
        else:
            self.vector_store.add_documents(documents)

        self.save()
        return len(documents)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[MetadataFilter] = None,
    ) -> List[Tuple[Document, float]]:
        if self.vector_store is None:
            return []

        k = min(max(k, 1), self.vector_store.index.ntotal)
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
        if score_threshold is not None:
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores if score <= score_threshold
            ]
        if metadata_filter is not None:
            docs_with_scores = [
                (doc, score) for doc, score in docs_with_scores if metadata_filter(doc)
            ]
        return docs_with_scores

    def _all_documents(self) -> List[Document]:
        if self.vector_store is None:
            return []

        documents: List[Document] = []
        for docstore_id in self.vector_store.index_to_docstore_id.values():
            document = self.vector_store.docstore._dict.get(docstore_id)
            if document is not None:
                documents.append(document)
        return documents

    def get_documents_by_reference(self, doc_id: str, source: Optional[str] = None) -> List[Document]:
        documents = self._all_documents()
        return [
            document
            for document in documents
            if document.metadata.get("doc_id") == doc_id
            or (
                source
                and document.metadata.get("source") == source
                and not document.metadata.get("doc_id")
            )
        ]

    def _clear_persisted_files(self) -> None:
        for path in (self.index_file, self.metadata_file):
            if os.path.exists(path):
                os.remove(path)

    def delete_documents_by_reference(self, doc_id: str, source: Optional[str] = None) -> int:
        documents = self._all_documents()
        if not documents:
            return 0

        remaining_documents = [
            document
            for document in documents
            if not (
                document.metadata.get("doc_id") == doc_id
                or (
                    source
                    and document.metadata.get("source") == source
                    and not document.metadata.get("doc_id")
                )
            )
        ]
        removed_count = len(documents) - len(remaining_documents)
        if removed_count == 0:
            return 0

        if remaining_documents:
            self.vector_store = FAISS.from_documents(
                documents=remaining_documents,
                embedding=self.embeddings
            )
            self.save()
        else:
            self.vector_store = None
            self._clear_persisted_files()

        return removed_count

    def is_empty(self) -> bool:
        return self.vector_store is None or self.vector_store.index.ntotal == 0

    def get_document_count(self) -> int:
        if self.vector_store is None:
            return 0
        return self.vector_store.index.ntotal
