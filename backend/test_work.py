"""Quick smoke test for Work IQ (analyst briefing context).

Run from backend/:
  source .venv/bin/activate && python test_work.py
Or:
  .venv/bin/python test_work.py
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
        import pytz  # noqa: F401
    except ModuleNotFoundError:
        if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
            os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])
        raise SystemExit(
            "pytz not installed for this Python.\n"
            "Fix:\n"
            "  cd backend\n"
            "  source .venv/bin/activate\n"
            "  pip install -r ../requirements.txt\n"
            "  python test_work.py"
        ) from None


_ensure_dependencies()

from fintelliops_iq.work_iq import WorkIQClient

work = WorkIQClient()

print("Health:", work.health_check())
print("\nANL-001 context:", work.get_analyst_context("ANL-001"))
print("\nANL-002 context:", work.get_analyst_context("ANL-002"))
print("\nOptimal briefing (ANL-001):", work.get_optimal_briefing_time("ANL-001"))
print("\nDeliver now? (ANL-001):", work.should_deliver_briefing("ANL-001"))
print("\nTeam summary:", work.get_team_summary())
