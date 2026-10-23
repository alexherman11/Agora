"""Build a hash-bound, inactive candidate. Never applies to source or the world."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "text-desk-lab" / "notation"


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one exact source anchor: {old!r}")
    return text.replace(old, new, 1)


HELPERS = '''

def policy(w):
    """Opt in through one world-authored policy note; absent/ambiguous = legacy."""
    notes = [s for s in w.subjects.values()
             if (s.get("props") or {}).get("role") == "task-transition-policy"]
    if len(notes) != 1:
        return None
    p = notes[0].get("props") or {}
    if p.get("version") != "1" or p.get("enabled") != "on":
        return None
    return p


def comment_lead(w, s):
    """Only the task's implicit destination changes; explicit addresses still win."""
    p = (s or {}).get("props") or {}
    if policy(w) and (s or {}).get("kind") in {"task", "story", "epic"}:
        return p.get("lead") or p.get("asked_by") or ""
    return ""


def accept_notice(state, notice):
    """Queue-receipt index, saved WITH inbox/cursor by news(), not model delivery.

    Per task/reason/recipient high water marks prevent duplicate event passes,
    including an older event replayed after a later one. This function never sends,
    retries or reads a provider's pending/unknown delivery state.
    """
    if not notice.get("action_keys"):
        return notice
    seen = state.setdefault("task_notice_receipts", {})
    fresh = []
    for kind, key in zip(notice["kinds"], notice["action_keys"]):
        if int(notice["event"][1:]) > int(seen.get(key, "e0")[1:]):
            fresh.append(kind)
    if not fresh:
        return None
    for key in notice["action_keys"]:
        previous = seen.get(key, "e0")
        if int(notice["event"][1:]) > int(previous[1:]):
            seen[key] = notice["event"]
    return dict(notice, kinds=fresh)
'''


def candidates():
    originals = {n: (LAB / n).read_text(encoding="utf-8")
                 for n in ("task_flow.py", "house.py", "rooms.py")}
    out = dict(originals)
    t = out["task_flow.py"]
    t = once(t, "\ndef notices(w, event):", HELPERS + "\n\ndef notices(w, event):")
    t = once(t, '    recipients = {}\n', '    recipients = {}\n    eligibility = policy(w)\n')
    t = once(t, '    if state in STATES:\n',
             '    states = set(eligibility.get("states", "").split(",")) if eligibility else STATES\n'
             '    if state in states:\n')
    t = once(t, '    if changed.intersection(BLOCK_FIELDS):\n',
             '    block_change = bool(changed.intersection(BLOCK_FIELDS))\n'
             '    if eligibility:\n'
             '        block_change = bool(props.get("blocked_on") and props.get("blocker_owner")\n'
             '                            and (block_change or "lead" in changed or "asked_by" in changed))\n'
             '    if block_change:\n')
    t = once(t, '        and props.get("worker_milestone") in MILESTONES\n',
             '        and props.get("worker_milestone") in (\n'
             '            set(eligibility.get("milestones", "").split(",")) if eligibility else MILESTONES)\n'
             '        and (not eligibility or "worker_milestone" in changed)\n')
    t = once(t, '            "kinds": kinds,\n',
             '            "kinds": kinds,\n'
             '            # Native event identity is the action epoch, not summary prose.\n'
             '            # Kind and recipient are independent: a new resolver is never deduped away.\n'
             '            "action_keys": [f"{card.get(\'id\') or event[\'target\']}:{actor}:{kind}"\n'
             '                            for kind in kinds] if eligibility else [],\n')
    out["task_flow.py"] = t
    t = out["house.py"]
    t = once(t, '            return bool(s) and persons.holds(w, (s.get("props") or {}).get("asked_by") or "", actor)',
             '            return bool(s) and persons.holds(w, task_flow.comment_lead(w, s)\n'
             '                or (s.get("props") or {}).get("asked_by") or "", actor)')
    t = once(t, '                        inbox.append(task_flow.delivery_text(notice))',
             '                        notice = task_flow.accept_notice(r.state, notice)\n'
             '                        if notice is None:\n'
             '                            continue\n'
             '                        inbox.append(task_flow.delivery_text(notice))')
    t = once(t, '                if not (e["verb"] == "comment" and asked(s)):',
             '                if not (e["verb"] == "comment" and (asked(s) or (\n'
             '                    task_flow.comment_lead(w, s) and any(\n'
             '                        rooms.same_person(w, x, actor) for x in rooms.comment_to(e))))):')
    t = once(t, '            elif rooms.comment_falls_back(e) and sid in mine:',
             '            elif rooms.comment_falls_back(e) and sid in mine and not task_flow.comment_lead(w, s):')
    out["house.py"] = t
    t = out["rooms.py"]
    t = once(t, '        asked = comment and persons.holds(w, (s.get("props") or {}).get("asked_by") or "", actor)',
             '        asked = comment and persons.holds(w, task_flow.comment_lead(w, s)\n'
             '            or (s.get("props") or {}).get("asked_by") or "", actor)')
    t = once(t, '        if by == "house" and not asked:',
             '        if by == "house" and not (asked or (task_flow.comment_lead(w, s)\n'
             '                and any(same_person(w, x, actor) for x in named))):')
    t = once(t, '        called = any(same_person(w, x, actor) for x in named)',
             '        if comment and task_flow.comment_lead(w, s):\n'
             '            mine = False  # implicit card route is its lead, never its containing corner\n'
             '        called = any(same_person(w, x, actor) for x in named)')
    out["rooms.py"] = t
    return originals, out


def main():
    originals, out = candidates()
    chunks = []
    manifest = {}
    for name, content in out.items():
        path = f"research/text-desk-lab/notation/{name}"
        chunks.extend(difflib.unified_diff(originals[name].splitlines(True),
                                          content.splitlines(True),
                                          fromfile="a/" + path, tofile="b/" + path))
        manifest[path] = {
            "base_raw_sha256": hashlib.sha256((LAB / name).read_bytes()).hexdigest(),
            "base_sha256": hashlib.sha256(originals[name].encode()).hexdigest(),
            "candidate_sha256": hashlib.sha256(content.encode()).hexdigest(),
        }
    patch = "".join(chunks)
    (HERE / "candidate.patch").write_text(patch, encoding="utf-8")
    manifest["patch_sha256"] = hashlib.sha256(patch.encode()).hexdigest()
    manifest["patch_raw_sha256"] = hashlib.sha256((HERE / "candidate.patch").read_bytes()).hexdigest()
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
