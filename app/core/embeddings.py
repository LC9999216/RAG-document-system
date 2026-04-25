import os
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv

load_dotenv()


class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)
        return embedding[0].tolist()

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)


# Cached embedding model instance
_embedding_model: Optional[LocalEmbeddings] = None


def get_embedding_model() -> LocalEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _embedding_model = LocalEmbeddings(model_name=model_name)
    return _embedding_model


def get_embeddings(texts: List[str]) -> List[List[float]]:
    embeddings = get_embedding_model()
    return embeddings.embed_documents(texts)
