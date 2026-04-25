import io
import tempfile
from typing import List
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def load_pdf(file_path: str) -> List[Document]:
    loader = PyPDFLoader(file_path)
    return loader.load()


def load_pdf_from_bytes(pdf_bytes: bytes, file_name: str = "uploaded_file.pdf") -> List[Document]:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(pdf_bytes)
        tmp_file.flush()

    try:
        loader = PyPDFLoader(str(tmp_path))
        documents = loader.load()

        for doc in documents:
            doc.metadata["source"] = file_name

        return documents
    finally:
        tmp_path.unlink(missing_ok=True)


def load_markdown(file_path: str) -> List[Document]:
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()


def load_markdown_from_bytes(md_bytes: bytes, file_name: str = "uploaded_file.md") -> List[Document]:
    text = md_bytes.decode("utf-8")
    doc = Document(
        page_content=text,
        metadata={
            "source": file_name,
            "page": 1,
        }
    )
    return [doc]
