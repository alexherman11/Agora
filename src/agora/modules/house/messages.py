"""House messages are direct sections of the live Agent Book, never source copies."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kernel.text_templates import render


def message(see, heading, **facts):
    return render(see, "Agent Book", heading, facts)
