"""Short-lived interactive previews backed by disposable copies, scoped to their caller.
Never: never changes the live world, supplies ambient authority, or persists preview sessions."""

import atexit
import secrets
import tempfile
import threading
import time

from kernel import component_commands as commands
from kernel import component_data as data
from kernel import events, store

_sessions = {}
_lock = threading.RLock()


def close(world, actor, token):
    with _lock:
        session = _sessions.get(token)
        if session and session["owner"] != (str(world.world.path), actor):
            raise ValueError("candidate belongs to a different caller")
        if session:
            _dispose(token)
    return {"closed": True}


def _dispose(token):
    session = _sessions.pop(token)
    session["world"].close()
    session["directory"].cleanup()


def open_candidate(world, actor, entity, revision, viewport):
    with _lock:
        for token, session in list(_sessions.items()):
            if session["expires"] < time.monotonic():
                _dispose(token)
        if len(_sessions) >= 8:
            raise ValueError("close an existing preview before opening another")
        record = data.definition(world, entity, revision)
        directory = tempfile.TemporaryDirectory(prefix="agora-interactive-candidate-")
        candidate = None
        try:
            candidate_world = events.open_world(directory.name)
            events.copy_log(world.world, candidate_world)
            candidate = store.open_store(candidate_world)
            frame = commands.frame(candidate, entity, record.revision, viewport=viewport)
            token = secrets.token_urlsafe(24)
            _sessions[token] = {
                "owner": (str(world.world.path), actor),
                "world": candidate,
                "directory": directory,
                "entity": entity,
                "revision": record.revision,
                "expires": time.monotonic() + 300,
            }
            return dict(frame, candidate=token)
        except BaseException:
            if candidate:
                candidate.close()
            directory.cleanup()
            raise


def interact(world, actor, token, event, fingerprint, local, viewport, commit):
    with _lock:
        session = _sessions.get(token)
        if not session or session["owner"] != (str(world.world.path), actor):
            raise ValueError("unknown or inaccessible candidate")
        if session["expires"] < time.monotonic():
            _dispose(token)
            raise ValueError("preview expired; open a fresh candidate")
        session["expires"] = time.monotonic() + 300
        frame = commands.interact(
            session["world"],
            actor,
            session["entity"],
            session["revision"],
            event,
            local,
            viewport,
            fingerprint,
            commit,
            candidate=True,
        )
        return dict(frame, candidate=token)


def cleanup():
    with _lock:
        for token in list(_sessions):
            _dispose(token)


atexit.register(cleanup)
