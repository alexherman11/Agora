"""Load trusted voice source as an isolated generation between calls.
Never reload the model runtime, accept source paths from callers, or mutate a live module.
"""

import hashlib
from pathlib import Path

from agora3.world import Refusal

ROOT = Path(__file__).parent
NAMES = ("voice_context", "voice_transport", "voice_coordination", "voice_session")


def load():
    sources = {name: (ROOT / (name + ".py")).read_bytes() for name in NAMES}
    version = hashlib.sha256(b"".join(sources.values())).hexdigest()[:16]
    # Compile everything before executing; failed generations never replace live factories.
    compiled = {
        name: compile(source, str(ROOT / (name + ".py")), "exec")
        for name, source in sources.items()
    }
    modules = {}
    for name in NAMES:
        namespace = {
            "__name__": "agora3._reload_" + name + "_" + version,
            "__package__": "agora3",
            "__file__": str(ROOT / (name + ".py")),
        }
        exec(compiled[name], namespace)
        modules[name] = namespace
    context = modules["voice_context"]
    modules["voice_coordination"]["spoken_chunks"] = context["spoken_chunks"]
    modules["voice_session"].update(
        Transcript=context["Transcript"],
        spoken_chunks=context["spoken_chunks"],
        Coordination=modules["voice_coordination"]["Coordination"],
    )
    exports = {
        "connect": modules["voice_transport"]["LiveConnection"],
        "session_factory": modules["voice_session"]["VoiceSession"],
        "configuration": context["configuration"],
        "model": context["MODEL"],
        "voice": context["VOICE"],
        "version": version,
    }
    if not all(callable(exports[key]) for key in ("connect", "session_factory", "configuration")):
        raise Refusal("Voice source does not expose the required runtime factories.")
    return exports
