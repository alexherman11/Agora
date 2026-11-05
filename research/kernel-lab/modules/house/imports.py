"""Copy one landed Git blob into a definition, through normal kernel admission.

No checkout reads, installer execution, module-own writes, credentials or Git writes.
The only destinations supported by this word are component.code and lens.text;
review marks, grants, identities and settings are deliberately not destinations.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import PurePosixPath

ID = re.compile(r"[a-z]{2,4}[0-9]+\Z")
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
FIELDS = {("component", "code"), ("lens", "text")}
MAX_BYTES = 1024 * 1024
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def git(repo, *args):
    """Only read operations are issued below; bytes never pass through text-mode CRLF conversion."""
    result = subprocess.run(
        ["git", "--no-optional-locks", "--no-replace-objects", "--literal-pathspecs", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=3, creationflags=NO_WINDOW)
    if result.returncode:
        raise ValueError("committed main or recorded landing is unavailable")
    return result.stdout


def path_arg(value):
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(ord(c) < 32 for c in value) or value.startswith("/")
            or any(p in ("", ".", "..") for p in value.split("/"))
            or PurePosixPath(value).is_absolute()):
        raise ValueError("path must be a repository-relative file without traversal")
    return value


def landing(builders, card):
    """Find a House-owned receipt, including a superseded worker of this card.

Never infer review_base from a merge parent, a caller-supplied revision, or task text.
The visible card selects the landed commit; a missing/ambiguous receipt refuses.
"""
    task, commit = card["id"], str(card.get("landed_commit", ""))
    if not OID.fullmatch(commit):
        raise ValueError("from card has no recorded landed commit")
    states = list(builders.states.values())
    for path in builders.home.glob("*/state.json"):
        states.append(json.loads(path.read_text(encoding="utf-8")))
    bases = {s.get("review_base") for s in states
             if s.get("task") == task and s.get("phase") == "landed"
             and s.get("landed_commit") == commit}
    if len(bases) != 1 or not OID.fullmatch(str(next(iter(bases), ""))):
        raise ValueError("no unambiguous House landing receipt with review_base; do not guess a merge parent")
    return next(iter(bases)), commit


def tree_entry(repo, commit, path):
    data = git(repo, "ls-tree", "-z", commit, "--", path)
    entries = [row for row in data.split(b"\0") if row]
    if len(entries) != 1:
        raise ValueError("file is missing from committed main or the landing")
    header, name = entries[0].split(b"\t", 1)
    mode, kind, oid = header.decode("ascii").split()
    if name.decode("utf-8") != path or kind != "blob" or mode not in ("100644", "100755"):
        raise ValueError("only regular committed files may be imported; no symlinks or submodules")
    return mode, oid


def source(repo, base, commit, path):
    main = git(repo, "rev-parse", "--verify", "refs/heads/main^{commit}").decode("ascii").strip()
    git(repo, "merge-base", "--is-ancestor", commit, main)
    git(repo, "merge-base", "--is-ancestor", base, commit)
    changed = git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                  "--name-only", "--diff-filter=AM", "-z", base, commit, "--", path)
    if path.encode("utf-8") not in changed.split(b"\0"):
        raise ValueError("the recorded landing did not add or modify this file")
    mode, blob = tree_entry(repo, commit, path)
    if tree_entry(repo, main, path) != (mode, blob):
        raise ValueError("stale landing: this file differs on current committed main")
    size = int(git(repo, "cat-file", "-s", blob))
    if size > MAX_BYTES:
        raise ValueError("file exceeds the 1 MiB text import limit")
    data = git(repo, "cat-file", "blob", blob)
    if len(data) != size or b"\0" in data:
        raise ValueError("file is not importable UTF-8 text")
    text = data.decode("utf-8")
    return main, blob, text


def quote(text):
    # Lines uses shlex, not JSON string decoding: preserve literal newlines and escapes.
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def call(house, msg):
    """Synchronous declarative answer: late/denied answers cannot write anything."""
    try:
        args = msg.get("args") or {}
        kv = args.get("kv") or {}
        target, card_id = args.get("target"), kv.get("from")
        identity = msg.get("caller") or {}
        caller = identity.get("person")
        if (not msg.get("use") or not caller or not identity.get("id")
                or not house.builders.steward(caller)):
            raise ValueError("house.import is for authenticated stewards")
        from gaming_gate import assert_clear
        assert_clear()  # before Git reads or any world edit
        if (args.get("words") or set(kv) != {"field", "from", "path"}
                or not ID.fullmatch(str(target)) or not ID.fullmatch(str(card_id))):
            raise ValueError("use house.import <thing> field=code|text from=<landed-card> path=<file>")
        path, field = path_arg(kv["path"]), kv["field"]

        def look(thing):
            result = house.m.see("look " + thing, use=msg["use"])
            rows = result.get("rows") or []
            if result.get("refused") or result.get("ok") is False or not rows or rows[0].get("id") != thing:
                raise ValueError("source card or destination is not readable through this call")
            return rows[0]

        # Kernel module answers currently retain the person's rights but do not
        # recursively narrow every upstream module's field grants. Do not widen
        # that path here: only a direct steward/agent can request this import.
        # Automatic switch-on is explicitly outside this word's first increment.
        principal = look(identity["id"])
        # caller.person is the kernel-authenticated agent/person mapping; look's
        # agent summary intentionally omits its `for` field.
        if not ((principal.get("kind") == "person" and principal["id"] == caller)
                or principal.get("kind") == "agent"):
            raise ValueError("house.import needs a direct steward or steward's agent, not a module caller")
        current, card = look(target), look(card_id)
        if (current.get("kind"), field) not in FIELDS:
            raise ValueError("import supports only component.code or lens.text; no grant/security fields")
        # Do not wait for a long landing while holding a synchronous module call.
        if not house.builders.landing_lock.acquire(blocking=False):
            raise ValueError("a landing is in progress; retry after it finishes")
        try:
            base, commit = landing(house.builders, card)
            main, blob, value = source(house.builders.repo, base, commit, path)
            old = str(current.get(field, ""))
            old_hash, new_hash = digest(old), digest(value)
            same = old == value
            receipt = dict(status="unchanged" if same else "changed", landing=card_id,
                           review_base=base, commit=commit, main=main, path=path, blob=blob,
                           thing=target, field=field, old_sha256=old_hash, new_sha256=new_hash,
                           review=("unchanged" if current.get("reviewed_code") == new_hash else "required")
                           if field == "code" else "not-applicable",
                           grants="unchanged")
            assert_clear()
            if git(house.builders.repo, "rev-parse", "--verify", "refs/heads/main^{commit}").decode().strip() != main:
                raise ValueError("main advanced during import; retry against its current committed tree")
            # Always submit set, even on equality: normal caller/module field permissions
            # still apply. Kernel set equality creates no record and never reviews code.
            return dict(lines=[f"set {target} {field}={quote(value)}"],
                        saw={target: {"rev": int(current["rev"]), "participant": True},
                             card_id: {"rev": int(card["rev"]), "participant": True}},
                        text="house.import " + json.dumps(receipt, ensure_ascii=False, sort_keys=True),
                        rows=[receipt])
        finally:
            house.builders.landing_lock.release()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        return {"refused": str(exc)}
