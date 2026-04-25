import os
from typing import List, Optional, TypedDict

from langchain_core.documents import Document

from app.data.loader import load_markdown, load_markdown_from_bytes, load_pdf, load_pdf_from_bytes
from app.data.splitter import split_documents
from app.graphs.graph import GraphState, create_rag_graph
from app.storage.storage import StorageManager
from app.storage.vector_store import VectorStoreManager


class Citation(TypedDict):
    text: str
    source: str
    page: int
    score: float


class AskResponse(TypedDict):
    answer: str
    citations: List[Citation]
    question: str


class UploadResponse(TypedDict):
    success: bool
    message: str
    documents_count: int
    file_name: str
    document_id: Optional[str]


NO_DOCUMENTS_MESSAGE = "不知道。当前还没有已上传文档。"
NO_ANSWER_MESSAGE = "不知道。已上传文档中没有足够信息回答这个问题。"
SUMMARY_PROMPT = "请概括这份文档的主要内容，提炼重点，使用中文条目式表达，并只依据提供的文档内容作答。"


class RAGService:
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.storage_manager = StorageManager()
        self.rag_graph = create_rag_graph(self.vector_store_manager)

    def upload_file(self, file_path: str) -> UploadResponse:
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".pdf":
                documents = load_pdf(file_path)
            elif ext in {".md", ".markdown"}:
                documents = load_markdown(file_path)
            else:
                return UploadResponse(
                    success=False,
                    message="不支持的文件格式，仅支持 PDF 和 Markdown",
                    documents_count=0,
                    file_name=os.path.basename(file_path),
                    document_id=None,
                )

            chunks = split_documents(documents)
            doc_id = self.storage_manager.generate_document_id()
            file_name = os.path.basename(file_path)
            chunks = self._attach_chunk_metadata(chunks, doc_id, file_name)
            count = self.vector_store_manager.add_documents(chunks)
            doc_info = self.storage_manager.add_document(file_name, count, doc_id=doc_id)
            self.storage_manager.add_document_chunks(doc_id, self._build_chunk_records(chunks))

            return UploadResponse(
                success=True,
                message=f"成功处理 {count} 个文档块",
                documents_count=count,
                file_name=file_name,
                document_id=doc_info["id"],
            )
        except Exception as exc:
            return UploadResponse(
                success=False,
                message=f"上传失败: {str(exc)}",
                documents_count=0,
                file_name=os.path.basename(file_path),
                document_id=None,
            )

    def upload_file_from_bytes(self, file_bytes: bytes, file_name: str) -> UploadResponse:
        ext = os.path.splitext(file_name)[1].lower()

        try:
            if ext == ".pdf":
                documents = load_pdf_from_bytes(file_bytes, file_name)
            elif ext in {".md", ".markdown"}:
                documents = load_markdown_from_bytes(file_bytes, file_name)
            else:
                return UploadResponse(
                    success=False,
                    message="不支持的文件格式，仅支持 PDF 和 Markdown",
                    documents_count=0,
                    file_name=file_name,
                    document_id=None,
                )

            chunks = split_documents(documents)
            doc_id = self.storage_manager.generate_document_id()
            chunks = self._attach_chunk_metadata(chunks, doc_id, file_name)
            count = self.vector_store_manager.add_documents(chunks)
            doc_info = self.storage_manager.add_document(file_name, count, doc_id=doc_id)
            self.storage_manager.add_document_chunks(doc_id, self._build_chunk_records(chunks))

            return UploadResponse(
                success=True,
                message=f"成功处理 {count} 个文档块",
                documents_count=count,
                file_name=file_name,
                document_id=doc_info["id"],
            )
        except Exception as exc:
            return UploadResponse(
                success=False,
                message=f"上传失败: {str(exc)}",
                documents_count=0,
                file_name=file_name,
                document_id=None,
            )

    def ask_question(self, question: str, save_chat: bool = True, document_id: str = "") -> AskResponse:
        if not question or not question.strip():
            return AskResponse(answer="问题不能为空", citations=[], question=question)

        if self.vector_store_manager.is_empty():
            return AskResponse(answer=NO_DOCUMENTS_MESSAGE, citations=[], question=question)

        result: GraphState = self.rag_graph.invoke(question, document_id=document_id)
        citations = self._build_citations(result.get("matches", []))
        answer = result.get("answer", "") or NO_ANSWER_MESSAGE

        if save_chat:
            self.storage_manager.add_message("user", question, [])
            self.storage_manager.add_message("assistant", answer, citations)

        return AskResponse(answer=answer, citations=citations, question=question)

    def summarize_document(self, doc_id: str, save_chat: bool = False) -> AskResponse:
        document = self.storage_manager.get_document(doc_id)
        if document is None:
            return AskResponse(answer="未找到指定文档。", citations=[], question=SUMMARY_PROMPT)

        if self.vector_store_manager.is_empty():
            return AskResponse(answer=NO_DOCUMENTS_MESSAGE, citations=[], question=SUMMARY_PROMPT)

        chunks = self.vector_store_manager.get_documents_by_reference(doc_id, source=document["file_name"])
        if not chunks:
            return AskResponse(answer="未找到该文档的可用内容。", citations=[], question=SUMMARY_PROMPT)

        ordered_chunks = sorted(
            chunks,
            key=lambda chunk: (
                int(chunk.metadata.get("page", 0)),
                str(chunk.metadata.get("chunk_id", "")),
            ),
        )
        context = "\n\n".join(chunk.page_content for chunk in ordered_chunks[:8])
        answer = self.rag_graph._generate_node(
            {
                "question": SUMMARY_PROMPT,
                "document_id": doc_id,
                "matches": [(chunk, 0.0) for chunk in ordered_chunks[:8]],
                "documents": ordered_chunks[:8],
                "answer": "",
            }
        )["answer"]
        citations = self._build_citations([(chunk, 0.0) for chunk in ordered_chunks[:8]])

        if save_chat:
            self.storage_manager.add_message("assistant", answer, citations)

        return AskResponse(answer=answer, citations=citations, question=SUMMARY_PROMPT)

    def get_chat_history(self, limit: int = 50) -> dict:
        history = self.storage_manager.get_chat_history(limit)
        return {"history": history, "total": len(self.storage_manager.get_all_chat_history())}

    def get_all_chat_history(self) -> dict:
        history = self.storage_manager.get_all_chat_history()
        return {"history": history, "total": len(history)}

    def clear_chat_history(self) -> dict:
        self.storage_manager.clear_chat_history()
        return {"success": True, "message": "对话历史已清空"}

    def get_documents(self) -> dict:
        docs = self.storage_manager.get_documents()
        return {"documents": docs, "total": len(docs)}

    def delete_document(self, doc_id: str) -> dict:
        document = self.storage_manager.get_document(doc_id)
        if document is None:
            return {"success": False, "message": "文档未找到"}

        removed_chunks = self.vector_store_manager.delete_documents_by_reference(
            doc_id,
            source=document["file_name"],
        )
        success = self.storage_manager.delete_document(doc_id)
        if success:
            return {"success": True, "message": f"文档已删除，并移除了 {removed_chunks} 个文档块"}
        return {"success": False, "message": "文档未找到"}

    def health_check(self) -> dict:
        docs = self.storage_manager.get_documents()
        return {
            "status": "healthy",
            "vector_store_loaded": not self.vector_store_manager.is_empty(),
            "document_count": self.vector_store_manager.get_document_count(),
            "saved_documents": len(docs),
            "chat_messages": len(self.storage_manager.get_all_chat_history()),
        }

    def _attach_chunk_metadata(self, chunks: List[Document], doc_id: str, file_name: str) -> List[Document]:
        prepared_chunks: List[Document] = []
        for index, chunk in enumerate(chunks):
            metadata = dict(chunk.metadata)
            metadata["doc_id"] = doc_id
            metadata["chunk_id"] = f"{doc_id}_chunk_{index}"
            metadata["source"] = file_name
            prepared_chunks.append(Document(page_content=chunk.page_content, metadata=metadata))
        return prepared_chunks

    def _build_chunk_records(self, chunks: List[Document]) -> List[dict]:
        return [
            {
                "chunk_id": chunk.metadata["chunk_id"],
                "source": chunk.metadata.get("source", "unknown"),
                "page": int(chunk.metadata.get("page", 0)),
            }
            for chunk in chunks
        ]

    def _build_citations(self, matches: List[tuple]) -> List[Citation]:
        citations: List[Citation] = []
        seen: set[tuple] = set()
        for doc, score in matches:
            citation = Citation(
                text=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                page=int(doc.metadata.get("page", 0)),
                score=round(float(score), 4),
            )
            key = (citation["source"], citation["page"], citation["text"])
            if key in seen:
                continue
            seen.add(key)
            citations.append(citation)
        return citations
