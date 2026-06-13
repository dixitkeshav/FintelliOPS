"""Index FintelliOps financial documents into Azure AI Search."""
from __future__ import annotations

import traceback

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Index FintelliOps knowledge documents into Azure AI Search"

    def handle(self, *args, **options) -> None:
        try:
            from fintelliops_iq.indexer import index_all_documents

            count = index_all_documents()
            if count:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Knowledge base indexed — {count} chunks uploaded")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠ Azure Search not configured — skipping")
                )
        except Exception:
            traceback.print_exc()
            raise SystemExit(1) from None
