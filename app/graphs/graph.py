import os
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.llm import generate_answer, get_llm
from app.storage.vector_store import VectorStoreManager

TOP_K = int(os.getenv("TOP_K", "8"))
RETRIEVAL_SCORE_THRESHOLD = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "1.35"))
NO_ANSWER_MESSAGE = "不知道。已上传文档中没有足够信息回答这个问题。"

QUERY_SYNONYMS = {
    "机遇": {"机会", "方向", "赛道", "增长点"},
    "机会": {"机遇", "方向", "赛道", "增长点"},
    "方面": {"方向", "领域", "赛道"},
    "未来": {"2035", "未来十年"},
    "趋势": {"方向", "格局"},
    "概括": {"总结", "摘要", "概述"},
    "总结": {"概括", "摘要", "概述"},
}


class GraphState(TypedDict):
    question: str
    document_id: str
    matches: list
    documents: list
    answer: str


class RAGGraph:
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(GraphState)

        workflow.add_node("query", self._query_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)

        workflow.set_entry_point("query")
        workflow.add_edge("query", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def _query_node(self, state: GraphState) -> GraphState:
        question = state["question"].strip()
        document_id = state.get("document_id", "").strip()
        return {"question": question, "document_id": document_id, "matches": [], "documents": [], "answer": ""}

    def _retrieve_node(self, state: GraphState) -> GraphState:
        question = state["question"]
        document_id = state.get("document_id", "")

        if self.vector_store_manager.is_empty():
            return {"question": question, "document_id": document_id, "matches": [], "documents": [], "answer": ""}

        retrieval_query = self._build_retrieval_query(question)
        docs_with_scores = self.vector_store_manager.similarity_search(
            retrieval_query,
            k=TOP_K,
            score_threshold=RETRIEVAL_SCORE_THRESHOLD,
            metadata_filter=self._document_filter(document_id),
        )
        docs_with_scores = self._rerank_matches(question, docs_with_scores)
        documents = [doc for doc, _ in docs_with_scores]

        return {
            "question": question,
            "document_id": document_id,
            "matches": docs_with_scores,
            "documents": documents,
            "answer": "",
        }

    def _generate_node(self, state: GraphState) -> GraphState:
        question = state["question"]
        document_id = state.get("document_id", "")
        matches = state["matches"]
        documents = state["documents"]

        if not documents:
            return {
                "question": question,
                "document_id": document_id,
                "matches": [],
                "documents": [],
                "answer": NO_ANSWER_MESSAGE,
            }

        context_parts = []
        for doc, score in matches:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", 0)
            content = doc.page_content
            context_parts.append(f"[来源: {source}, 页码: {page}, 分数: {score:.4f}]\n{content}")

        context = "\n\n".join(context_parts)

        llm = get_llm(temperature=0.2)
        answer = generate_answer(context, question, llm)

        return {
            "question": question,
            "document_id": document_id,
            "matches": matches,
            "documents": documents,
            "answer": answer,
        }

    def invoke(self, question: str, document_id: str = "") -> GraphState:
        return self.graph.invoke(
            {"question": question, "document_id": document_id, "matches": [], "documents": [], "answer": ""}
        )

    def _rerank_matches(self, question: str, docs_with_scores: list[tuple]) -> list[tuple]:
        if not docs_with_scores:
            return []

        query_terms = self._extract_terms(self._build_retrieval_query(question))
        ranked_matches = []
        for doc, score in docs_with_scores:
            doc_terms = self._extract_terms(doc.page_content)
            lexical_overlap = len(query_terms & doc_terms) if query_terms else 0
            ranked_matches.append((lexical_overlap, score, doc))

        if query_terms and any(overlap > 0 for overlap, _, _ in ranked_matches):
            ranked_matches = [item for item in ranked_matches if item[0] > 0]

        ranked_matches.sort(key=lambda item: (-item[0], item[1]))
        return [(doc, score) for overlap, score, doc in ranked_matches]

    def _extract_terms(self, text: str) -> set[str]:
        ascii_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9_]+", text)
            if len(term) >= 2
        }

        cjk_chunks = re.findall(r"[\u4e00-\u9fff]+", text)
        cjk_terms: set[str] = set()
        for chunk in cjk_chunks:
            normalized = chunk.strip()
            if not normalized:
                continue
            if len(normalized) >= 2:
                cjk_terms.add(normalized)
                cjk_terms.update(
                    normalized[index:index + 2]
                    for index in range(len(normalized) - 1)
                )
            else:
                cjk_terms.add(normalized)

        return ascii_terms | cjk_terms

    def _build_retrieval_query(self, question: str) -> str:
        terms = self._extract_terms(question)
        expanded_terms = set(terms)
        for term in terms:
            expanded_terms.update(QUERY_SYNONYMS.get(term, set()))
        expanded_terms.add(question.strip())
        return " ".join(sorted(term for term in expanded_terms if term))

    def _document_filter(self, document_id: str):
        if not document_id:
            return None
        return lambda document: document.metadata.get("doc_id") == document_id


def create_rag_graph(vector_store_manager: VectorStoreManager) -> RAGGraph:
    return RAGGraph(vector_store_manager)
