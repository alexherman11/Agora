"""Direct-child launch receipts, not discovery or same-user authentication.

Parent/profile/desktop are immutable *launch facts*, not observations of an
engine's later profile or of delegated children. A later exact PID/FILETIME/
image match identifies that same birth; it does not certify a whole runtime.
"""
import ntpath

from sandbox_receipts import complete, path_key

METHOD = "CreateProcessW-suspended-v1"


def intent(argv, parent, desktop):
    if not argv or not ntpath.isabs(argv[0]):
        raise ValueError("an absolute executable is required")
    if not desktop.startswith("WinSta0\\agora-sandbox-"):
        raise ValueError("a sandbox desktop is required")
    profiles = []
    for i, arg in enumerate(argv):
        for flag in ("--user-data-dir", "--sandbox-profile"):
            if arg.startswith(flag + "="):
                profiles.append(arg[len(flag) + 1:])
            elif arg == flag:
                profiles.append(argv[i + 1] if i + 1 < len(argv) else "")
    if len(profiles) > 1 or (profiles and not ntpath.isabs(profiles[0])):
        raise ValueError("ambiguous or relative profile")
    return {"method": METHOD, "exe": path_key(argv[0]), "parent": dict(parent),
            "profile": path_key(profiles[0]) if profiles else "", "desktop": desktop,
            "profile_scope": "launch argument only"}


def capture(launch, pid, identity):
    if identity is None or path_key(identity[1]) != launch["exe"]:
        raise ValueError("created child executable does not match launch")
    result = {**launch, "pid": pid, "created": identity[0]}
    if not valid(result) or result["parent"]["created"] > result["created"]:
        raise ValueError("created child identity incomplete")
    return result


def valid(owner):
    return (complete(owner) and owner.get("method") == METHOD
            and isinstance(owner.get("desktop"), str)
            and owner["desktop"].startswith("WinSta0\\agora-sandbox-")
            and owner.get("profile_scope") == "launch argument only"
            and owner["parent"]["created"] <= owner["created"])


def bound(state, owner):
    """Detect inconsistent launch/owner copies; files are NOT authentication."""
    if not valid(owner):
        return False
    records = [r for r in state.get("launches", [])
               if isinstance(r, dict) and r.get("pid") == owner["pid"]]
    if len(records) != 1:
        return False
    record = records[0]
    facts = record.get("intent")
    return (record.get("owner") == owner
            and record.get("status") in ("resume-pending", "resume-unknown", "running")
            and isinstance(facts, dict)
            and facts == {k: owner[k] for k in (
                "method", "exe", "parent", "profile", "desktop", "profile_scope")})


def persist_then_resume(state, launch, owner, persist, resume):
    """A persistence failure never executes resume. Unknown resume never retries."""
    state.setdefault("owners", []).append(owner)
    launch.update(status="resume-pending", pid=owner["pid"], owner=dict(owner))
    persist(state)
    result = resume()
    if result != 1:
        # CREATE_SUSPENDED has exactly one suspension. Do not decrement again.
        launch.update(status="resume-unknown", resume_result=int(result))
        persist(state)
        raise RuntimeError("child resume did not confirm expected suspend count")
    launch.update(status="running", resume_result=1)
    persist(state)
