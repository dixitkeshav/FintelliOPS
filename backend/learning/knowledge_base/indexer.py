"""Index synthetic knowledge documents into Azure AI Search."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


def _get_config() -> tuple[str, str, str]:
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "").strip()
    key = os.getenv("AZURE_SEARCH_KEY", "")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")
    return endpoint, key, index_name


def create_index(index_client: SearchIndexClient, index_name: str) -> None:
    try:
        index_client.get_index(index_name)
        logger.info("Index already exists")
        return
    except Exception:
        pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
            analyzer_name="en.lucene",
        ),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
    ]
    index_client.create_index(SearchIndex(name=index_name, fields=fields))
    logger.info("Created index %s", index_name)


def _infer_doc_type(filename: str) -> str:
    lower = filename.lower()
    if "guide" in lower:
        return "guide"
    if "report" in lower:
        return "report"
    if "insights" in lower:
        return "insights"
    return "knowledge"


def chunk_document(filepath: str) -> list[dict]:
    path = Path(filepath)
    text = path.read_text(encoding="utf-8")
    words = text.split()
    filename = path.name
    doc_type = _infer_doc_type(filename)
    chunks: list[dict] = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    chunk_index = 0
    for i in range(0, len(words), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        if not chunk_words:
            break
        safe_name = path.stem.replace(".", "_")
        chunks.append(
            {
                "id": f"{safe_name}-chunk-{chunk_index}",
                "content": " ".join(chunk_words),
                "source": filename,
                "doc_type": doc_type,
                "chunk_index": chunk_index,
            }
        )
        chunk_index += 1
    return chunks


def index_all_documents(docs_path: str) -> int:
    endpoint, key, index_name = _get_config()
    if not endpoint or not key:
        raise RuntimeError("Azure Search not configured")

    index_client = SearchIndexClient(endpoint, AzureKeyCredential(key))
    create_index(index_client, index_name)
    search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

    all_chunks: list[dict] = []
    for md_file in Path(docs_path).glob("*.md"):
        all_chunks.extend(chunk_document(str(md_file)))

    if all_chunks:
        search_client.upload_documents(all_chunks)

    print(f"Indexed {len(all_chunks)} chunks from {docs_path}")
    return len(all_chunks)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data" / "documents"
    index_all_documents(str(base))
