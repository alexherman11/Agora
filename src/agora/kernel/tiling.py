"""Read-only browser seam to the desktop's one geometry engine.

No world facts, native references, sessions or persistent gesture state enter
the engine. A drop continues through the painter's existing fenced word.
"""
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().parents[2] / 'desktop' / 'agora-wm' / 'engine.py'
_spec = importlib.util.spec_from_file_location('_agora_tiling', _path)
_engine = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _engine
_spec.loader.exec_module(_engine)

def preview(body, kernel=None, actor=None):
    result = _engine.card_drop(body)
    if kernel is not None and actor is not None:
        # Host presentation settings, read under the viewer's visibility. No
        # facts or authority from the request enter this read or its response.
        with kernel.lock:
            settings = [a for tid in kernel.things('wm-settings')
                        if (a := kernel.shown(actor.person, tid)) is not None]
            if len(settings) == 1:
                try:
                    duration = int(settings[0].get('motion_ms', result['motion_ms']))
                    if 0 <= duration <= 1000:
                        result['motion_ms'] = duration
                except (ValueError, TypeError):
                    pass
    return result
