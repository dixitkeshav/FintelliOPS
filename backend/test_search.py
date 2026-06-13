"""Quick smoke test for Azure AI Search credentials and index.

Run from backend/:
  source .venv/bin/activate && python test_search.py
Or:
  .venv/bin/python test_search.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _SCRIPT_DIR / ".venv" / "bin" / "python"


def _ensure_dependencies() -> None:
    try:
        import azure.core.credentials  # noqa: F401
    except ModuleNotFoundError:
        if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
            os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])
        raise SystemExit(
            "Azure SDK not installed for this Python.\n"
            "Fix:\n"
            "  cd backend\n"
            "  source .venv/bin/activate\n"
            "  pip install -r ../requirements.txt\n"
            "  python test_search.py"
        ) from None


_ensure_dependencies()

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

load_dotenv(_SCRIPT_DIR / ".env")

endpoint = (os.getenv("AZURE_SEARCH_ENDPOINT") or "").strip()
key = os.getenv("AZURE_SEARCH_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")

if not endpoint or not key:
    raise SystemExit(
        "Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in backend/.env"
    )

client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(key),
)

query = "market"
results = list(
    client.search(
        search_text=query,
        top=3,
        select=["content", "source", "doc_type"],
    )
)

print(f"Index: {index_name}")
print(f"Query: {query!r}")
print(f"Documents found: {len(results)}")

if not results:
    print("No documents in index — run: python manage.py index_knowledge_base")
else:
    for r in results:
        source = r.get("source", "unknown")
        score = r.get("@search.score", 0)
        content = (r.get("content") or "")[:100]
        print(f"  - {source} (score: {score:.2f})")
        print(f"    {content}...")
