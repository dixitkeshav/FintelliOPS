"""Quick smoke test for Fabric IQ (networkx semantic graph).

Run from backend/:
  source .venv/bin/activate && python test_fabric.py
Or:
  .venv/bin/python test_fabric.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _SCRIPT_DIR / ".venv" / "bin" / "python"

if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


def _ensure_dependencies() -> None:
    try:
        import networkx  # noqa: F401
    except ModuleNotFoundError:
        if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
            os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])
        raise SystemExit(
            "networkx not installed for this Python.\n"
            "Fix:\n"
            "  cd backend\n"
            "  source .venv/bin/activate\n"
            "  pip install -r ../requirements.txt\n"
            "  python test_fabric.py"
        ) from None


_ensure_dependencies()

from fintelliops_iq.fabric_iq import FabricIQClient

fabric = FabricIQClient()

print("Health:", fabric.health_check())
print("\nTech sector:", fabric.get_sector_context("Technology"))
print("\nBanking companies:", fabric.get_companies_for_sector("SECT-002"))
print("\nFed rate correlations:", fabric.get_macro_correlations("US_FED_RATE"))
print("\nRisk at score 7.5:", fabric.get_risk_threshold(7.5))
print("\nCompany NVTK sector:", fabric.get_sector_for_company("NVTK"))
