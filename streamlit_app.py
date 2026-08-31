"""Cloud-compatible entrypoint for the Enterprise Decision Simulator."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))
runpy.run_path(str(SOURCE_ROOT / "decision_intelligence" / "app.py"), run_name="__main__")
