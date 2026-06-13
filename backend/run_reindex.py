"""Drop, recreate, and re-upload the Azure AI Search knowledge index.

Run from backend/:
  source .venv/bin/activate && python run_reindex.py
Or:
  .venv/bin/python run_reindex.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _SCRIPT_DIR / ".venv" / "bin" / "python"
_DOCS_DIR = _SCRIPT_DIR / "fintelliops_data" / "documents"


def _ensure_dependencies() -> None:
    try:
        import azure.search.documents  # noqa: F401
    except ModuleNotFoundError:
        if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
            os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])
        raise SystemExit(
            "Azure Search SDK not installed.\n"
            "Fix:\n"
            "  cd backend && source .venv/bin/activate\n"
            "  pip install -r ../requirements.txt\n"
            "  python run_reindex.py"
        ) from None


_ensure_dependencies()

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
)

from fintelliops_iq.indexer import chunk_document

load_dotenv(_SCRIPT_DIR / ".env")

endpoint = (os.getenv("AZURE_SEARCH_ENDPOINT") or "").strip()
key = os.getenv("AZURE_SEARCH_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")

if not endpoint or not key:
    raise SystemExit("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in backend/.env")

if not _DOCS_DIR.exists():
    raise SystemExit(f"Documents folder not found: {_DOCS_DIR}")

index_client = SearchIndexClient(endpoint, AzureKeyCredential(key))


def _build_index(with_semantic: bool) -> SearchIndex:
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
    if not with_semantic:
        return SearchIndex(name=index_name, fields=fields)

    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="source"),
            content_fields=[SemanticField(field_name="content")],
        ),
    )
    return SearchIndex(
        name=index_name,
        fields=fields,
        semantic_search=SemanticSearch(configurations=[semantic_config]),
    )


# 1. Delete old index
try:
    index_client.delete_index(index_name)
    print(f"Deleted old index: {index_name}")
except Exception as exc:
    print(f"No existing index to delete ({exc})")

# 2. Recreate index (semantic first, plain fallback for free tier)
try:
    index_client.create_index(_build_index(with_semantic=True))
    print(f"✓ Index recreated with semantic config: {index_name}")
except Exception as exc:
    print(f"Semantic index failed ({exc}) — falling back to standard index")
    index_client.create_index(_build_index(with_semantic=False))
    print(f"✓ Index recreated (standard): {index_name}")

# 3. Upload all document chunks
search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))
all_chunks: list[dict] = []
md_files = sorted(_DOCS_DIR.glob("*.md"))
for md_file in md_files:
    all_chunks.extend(chunk_document(str(md_file)))

if not all_chunks:
    raise SystemExit(f"No .md files found in {_DOCS_DIR}")

batch_size = 100
for i in range(0, len(all_chunks), batch_size):
    search_client.upload_documents(all_chunks[i : i + batch_size])

print(f"✓ Uploaded {len(all_chunks)} chunks from {len(md_files)} documents")
print("Done — run: python test_search.py")
