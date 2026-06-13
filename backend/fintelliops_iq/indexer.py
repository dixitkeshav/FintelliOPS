"""Index FintelliOps financial documents into Azure AI Search."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError
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
DOCS_DEFAULT = Path(__file__).resolve().parent.parent / "fintelliops_data" / "documents"


def _infer_doc_type(filename: str) -> str:
    lower = filename.lower()
    if "earnings" in lower:
        return "earnings"
    if "macro" in lower:
        return "macro"
    if "sector" in lower:
        return "sector"
    return "knowledge"


def create_index(index_client: SearchIndexClient, index_name: str) -> None:
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
    try:
        index_client.get_index(index_name)
        logger.info("Index already exists — skipping creation")
        return
    except Exception:
        pass
    index = SearchIndex(name=index_name, fields=fields)
    try:
        index_client.create_index(index)
        logger.info("Created index %s", index_name)
    except ResourceExistsError:
        logger.info("Index already exists — skipping creation")
    except Exception as exc:
        if "already exists" in str(exc).lower():
            logger.info("Index already exists — skipping creation")
        else:
            raise


def chunk_document(filepath: str) -> list[dict]:
    path = Path(filepath)
    words = path.read_text(encoding="utf-8").split()
    filename = path.name
    safe_name = path.stem.replace(".", "_")
    doc_type = _infer_doc_type(filename)
    chunks: list[dict] = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    chunk_index = 0
    for i in range(0, len(words), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        if not chunk_words:
            break
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


def index_all_documents(docs_path: str | None = None) -> int:
    endpoint = (os.getenv("AZURE_SEARCH_ENDPOINT", "") or "").strip()
    key = os.getenv("AZURE_SEARCH_KEY", "")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")

    if not endpoint or not key:
        print("⚠ Azure Search not configured — set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY")
        return 0

    path = Path(docs_path) if docs_path else DOCS_DEFAULT
    index_client = SearchIndexClient(endpoint, AzureKeyCredential(key))
    create_index(index_client, index_name)
    search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

    all_chunks: list[dict] = []
    md_files = list(path.glob("*.md"))
    for md_file in md_files:
        all_chunks.extend(chunk_document(str(md_file)))

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        search_client.upload_documents(all_chunks[i : i + batch_size])

    print(f"✓ Indexed {len(all_chunks)} chunks from {len(md_files)} documents")
    return len(all_chunks)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv("backend/.env")
    index_all_documents()
