from functools import lru_cache

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.rag_service import RAGService

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    document_id: str = ""


@lru_cache(maxsize=1)
def _build_rag_service() -> RAGService:
    return RAGService()


def get_rag_service() -> RAGService:
    try:
        return _build_rag_service()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"RAG service initialization failed: {exc}") from exc


@router.get("/health")
async def health_check(rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.health_check()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), rag_service: RAGService = Depends(get_rag_service)):
    file_bytes = await file.read()
    return rag_service.upload_file_from_bytes(file_bytes, file.filename)


@router.post("/ask")
async def ask_question(request: AskRequest, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.ask_question(request.question, document_id=request.document_id)


@router.get("/documents")
async def get_documents(rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.get_documents()


@router.get("/documents/{doc_id}/summary")
async def summarize_document(doc_id: str, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.summarize_document(doc_id)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.delete_document(doc_id)


@router.get("/chat/history")
async def get_chat_history(limit: int = 50, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.get_chat_history(limit)


@router.get("/chat/all")
async def get_all_chat_history(rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.get_all_chat_history()


@router.delete("/chat")
async def clear_chat_history(rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.clear_chat_history()
