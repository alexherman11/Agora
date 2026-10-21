"""Compatibility import for the original browsing experiment."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"))
from tab_history import Browser, Entry, NavigationError, Tab, Target, need  # noqa: E402,F401
