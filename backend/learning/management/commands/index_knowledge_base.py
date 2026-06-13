"""Django management command to index knowledge documents into Azure AI Search."""
from __future__ import annotations

import os
import traceback
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Index learning knowledge documents into Azure AI Search"

    def handle(self, *args, **options) -> None:
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "").strip()
        key = os.getenv("AZURE_SEARCH_KEY", "")

        if not endpoint or not key:
            self.stdout.write(
                self.style.WARNING(
                    "⚠ Azure Search not configured — local fallback active"
                )
            )
            return

        docs_path = Path(__file__).resolve().parents[2] / "data" / "documents"
        try:
            from learning.knowledge_base.indexer import index_all_documents

            count = index_all_documents(str(docs_path))
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Knowledge base indexed successfully ({count} chunks)"
                )
            )
        except Exception:
            traceback.print_exc()
            raise SystemExit(1) from None
