"""Small, recorded text changes for Lines, verbs, rules and buttons.

These are general words over text facts. The existing edit/set path supplies
validation, scoped writes, undo and CRDT history; no document-specific policy.
"""
import json
import re

from .bodies import edit, fingerprint
from .kernel import Refused
from .lines import Step


def _text(value):
    """Lines has already unquoted the value. Decode only documented escapes."""
    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\"}
    return re.sub(r"\\([nrt\\])", lambda m: escapes[m[1]], value)


def _headings(text):
    """ATX heading offsets, excluding fenced code."""
    fence, offset = None, 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        title = None if fence or marker else re.match(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", line.rstrip("\r\n"))
        if title:
            yield re.sub(r"[ \t]+#+[ \t]*$", "", title[1]), offset, offset + len(line)
        offset += len(line)


def _section(text, heading):
    headings = list(_headings(text))
    matches = [i for i, h in enumerate(headings) if h[0] == heading]
    if len(matches) > 1:
        raise Refused(f'heading "{heading}" is ambiguous; nothing changed')
    if not matches:
        return None
    i = matches[0]
    return headings[i][2], headings[i + 1][1] if i + 1 < len(headings) else len(text)


def _append_at(text, start, end, addition):
    # Keep every original character, including blank lines before the next heading.
    at = end
    while at > start and text[at - 1] in "\r\n":
        at -= 1
    prefix = "" if at == 0 or text[at - 1] == "\n" else "\n"
    suffix = "\n" if end < len(text) and at == end and not addition.endswith("\n") else ""
    return at, at, prefix + addition + suffix


def change(k, actor, st, entry, tx, group, saw=None):
    operation = entry["bound"].rsplit(".", 1)[-1]
    allowed = {"field", "heading", "text"} if operation == "append" else {"field", "heading", "old", "new"}
    if set(st.kv) - allowed or st.words:
        raise Refused(f"text.{operation} takes " + ", ".join(sorted(allowed)) + "= only")
    field = st.kv.get("field") or "text"
    if not field.replace("_", "").replace("-", "").isalnum() or field in ("kind", "id", "in", "as"):
        raise Refused("field= names one text fact, such as field=text")
    t = st.target
    shown = k.shown(actor.person, t)
    if shown is None:
        raise k.no_such(t)
    if k.state.get(t, field) is not None and field not in shown:
        raise Refused(f"{field}= is not visible; nothing changed")
    # A word does not lend a broader right than set, even if its entry is relaxed.
    set_entry = k.entry(k.find_entry("set", group))
    if not k.may(actor, set_entry, t, group):
        raise k.refusal_for(set_entry, group)
    current = tx.get(t, field, "")
    if not isinstance(current, str):
        raise Refused(f"{k.name(t)} {field}= is not text")
    k.reaches(actor, entry["word"], k.state.get(t, "kind"), target=t, fields={field: current}, group=group)
    k.reaches(actor, "set", k.state.get(t, "kind"), target=t, fields={field: current}, group=group)
    # A button keeps its painted fence; typed appends/anchored replacements use
    # the current text under the kernel lock, without resending a stale body.
    if saw is not None:
        k.fence(actor, t, [field], saw)
    heading = st.kv.get("heading")
    if heading is not None and (not heading.strip() or "\n" in heading or "\r" in heading):
        raise Refused("heading= needs a nonempty, single-line title without # markers")
    bounds = _section(current, heading) if heading is not None else (0, len(current))
    created, count = False, 0
    if operation == "append":
        if "text" not in st.kv or not st.kv["text"]:
            raise Refused("text.append needs nonempty text=")
        addition = _text(st.kv["text"])
        if bounds is None:
            separator = "" if not current else "\n" * (2 - min(2, len(current) - len(current.rstrip("\n"))))
            spans = [(len(current), len(current), separator + "## " + heading + "\n\n" + addition)]
            created = True
        elif heading is None:
            # Whole-note append is a strict prefix extension, even with trailing blanks.
            spans = [(len(current), len(current), ("" if not current or current.endswith("\n") else "\n") + addition)]
        else:
            spans = [_append_at(current, *bounds, addition)]
        count = 1
    else:
        if "new" not in st.kv:
            raise Refused("text.replace needs new= (new= alone deletes the matched text)")
        if bounds is None:
            raise Refused(f'heading "{heading}" not found; nothing changed')
        start, end = bounds
        replacement = _text(st.kv["new"])
        if "old" in st.kv:
            old = _text(st.kv["old"])
            if not old:
                raise Refused("old= must not be empty")
            spans, at = [], start
            while (at := current.find(old, at, end)) != -1:
                spans.append((at, at + len(old), replacement))
                at += len(old)
            if not spans:
                raise Refused("old= not found; nothing changed")
            count = len(spans)
        elif heading is not None:
            # Preserve the heading and its surrounding blank lines, not children.
            while start < end and current[start] in "\r\n":
                start += 1
            while end > start and current[end - 1] in "\r\n":
                end -= 1
            before = "\n" if start and current[start - 1] != "\n" else ""
            after = "\n" if end < len(current) and current[end] not in "\r\n" else ""
            spans = [(start, end, before + replacement + after)]
            count = 1
        else:
            raise Refused("text.replace needs old=, or heading= to replace its direct body")
    changes, position, units = [], 0, 0
    for a, b, value in spans:
        units += len(current[position:a].encode("utf-16-le")) // 2
        end_units = units + len(current[a:b].encode("utf-16-le")) // 2
        changes.append([units, end_units, value])
        position, units = b, end_units
    changed = any(current[a:b] != value for a, b, value in spans)
    edit_step = Step(st.text, "edit", t, {"field": field, "base": fingerprint(current),
                                       "changes": json.dumps(changes)}, "")
    out = edit(k, actor, edit_step, entry, tx, group, saw)
    description = ("appended" if operation == "append" else
                   "replaced section body" if "old" not in st.kv else f"replaced {count} match(es)") if changed else "unchanged"
    section = f' under "{heading}"' if heading is not None else ""
    receipt = " [r?]" if changed else ""
    out["text"] = f"ok {k.name(t)}{receipt} · {field}: {description}{section}" + (" (heading created)" if created else "")
    out["rows"][0].update(operation=operation, count=count, changed=changed, heading=heading, heading_created=created)
    return out
