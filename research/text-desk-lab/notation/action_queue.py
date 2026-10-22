"""Read-only grouped duties (a9377). Policy is world-authored; identities and evidence are not guesses.

Both source projections share one evaluation during scene.still(). Nothing is kept across builds.
See action-queue.md for the policy and authored question evidence vocabulary.
"""
import copy
import re

import knife
import persons
from world import Refusal


GROUP_FIELDS = ("key", "target", "title", "later", "reason_count", "counted", "uncertainty", "recipient", "item")
REASON_FIELDS = ("request_key", "kind", "source", "asker", "recipient", "resolution_state",
                 "resolution_evidence", "later", "eligible", "uncertainty", "key", "target",
                 "label", "asker_label", "recipient_label", "item")


def canonical(w, ref):
    """Only authored ids, never a title search."""
    return w.subject_of(ref) or (ref if ref in w.nodes else "")


def person(w, ref, event=None):
    if persons.is_pid(w, ref):
        return ref
    if event is not None:
        return persons.at(w, ref, int(event["id"][1:])) or ""
    return persons.resolve(w, ref)[0] or ""


def _policy(desk, ref):
    w = desk.world
    sid = w.subject_of(ref)
    s = w.subjects.get(sid, {})
    if s.get("kind") != "note":
        raise Refusal("actions policy must name an existing note")
    p = s.get("props") or {}
    required = ("action_designs", "action_reviews", "action_group_later", "action_review_later", "action_recipient")
    if any(not str(p.get(k, "")).strip() for k in required):
        raise Refusal("actions policy needs " + ", ".join(required) + "; use none for an empty selection")
    apps = set(w.appearances_of(sid))
    binding = next((e for e in reversed(w.events) if not e.get("undone")
                    and "action_recipient" in (e.get("args") or {})
                    and (e["target"] in apps | {sid}
                         or (e.get("undo") or {}).get("delete") in apps)), None)
    recipient = (person(w, p["action_recipient"], binding) if binding
                 else p["action_recipient"] if persons.is_pid(w, p["action_recipient"]) else "")
    if not recipient:
        raise Refusal("actions policy action_recipient must name a known person")
    sets = {}
    for k in (*required[:4], "action_question_news"):
        q = p.get(k, "none")
        if q == "none":
            sets[k] = set()
            continue
        hit = knife.parse_selection(w, q)
        if hit is None:
            raise Refusal(f"actions policy {k} must be a selection or none")
        sets[k] = {canonical(w, n) for n in hit[0]}
    labels = {kind: p.get(f"action_{kind}_label", kind) for kind in ("design", "review")}
    return sid, recipient, sets, labels, p


def _active_events(w):
    return [e for e in w.events if not e.get("undone") and e.get("verb") != "undo"]


def _origin(w, target, events, selection):
    """Find the current activation using retained before-images, without changing the world.

    A tag edit that leaves membership true is not a new request. If the before-image
    was externalized, refuse to guess its author: the reason becomes diagnostic.
    """
    shadow = copy.copy(w)
    shadow.nodes, shadow.subjects = dict(w.nodes), dict(w.subjects)
    shadow.__dict__.pop("_still_kids", None)
    apps = set(w.appearances_of(target)) if target in w.subjects else {target}
    for e in reversed(events):
        u = e.get("undo") or {}
        if u.get("delete_subject") == target or (target in w.nodes and u.get("delete") == target):
            return e
        if e.get("target") not in apps | {target} and target not in e.get("changed", []):
            continue
        before = u.get("restore_subject")
        if not before:
            before = next((s for s in u.get("restore_subjects", []) if s["id"] == target), None)
        if before and before["id"] == target:
            shadow.subjects[target] = before
        elif u.get("delete") in apps:
            shadow.nodes.pop(u["delete"], None)
        elif (u.get("restore") or {}).get("id") in apps | {target}:
            shadow.nodes[u["restore"]["id"]] = u["restore"]
        elif u.get("restore_props") and u["restore_props"][0] == target:
            shadow.nodes[target] = dict(shadow.nodes[target], props=u["restore_props"][1])
        elif e["verb"] in ("comment", "resolve", "markread"):
            if "comments" in knife.aspects_of(selection)[0]:
                return None
            continue
        else:
            return None
        before_selection = knife.parse_selection(shadow, selection)
        if before_selection is None:
            return None
        if target not in {canonical(shadow, n) for n in before_selection[0]}:
            return e
    return None


def _reason(kind, root, source, target, asker, recipient, **more):
    return dict(request_key=f"{kind}-{root}", kind=kind, source=source, target=target,
                asker=asker, recipient=recipient, resolution_state="open", resolution_evidence="",
                later="no", eligible="yes", uncertainty="", label=kind, **more)


def _questions(w, events):
    import scene
    comments = persons.comment_events(w)
    roots, replies = [], {}
    for s in w.subjects.values():
        for line in s.get("lines") or []:
            e = w.event_by_id(line.get("ev"))
            if not e or e.get("undone"):
                continue
            fields = scene.line_fields(line)
            row = dict(root=line["id"], source=line["id"], parent=s["id"], event=e, fields=fields,
                       to=[*(line.get("to") or []), *str((e.get("args") or {}).get("no_one", "")).split(",")],
                       about=fields.get("about", fields.get("context", (s.get("props") or {}).get("talk_of", ""))))
            if line.get("reply_to"):
                replies.setdefault(line["reply_to"], []).append(row)
            if fields.get("mark") == "ask":
                roots.append(row)
        for c in s.get("comments") or []:
            e = comments.get(c["id"])
            if not e or e.get("undone"):
                continue
            fields = dict(e.get("args") or {}, mark=c.get("mark", (e.get("args") or {}).get("mark", "")))
            if fields.get("mark") == "ask":
                roots.append(dict(root=c["id"], source=c["id"], parent=s["id"], event=e, fields=fields,
                                  to=e.get("to") or [], about=fields.get("about", s["id"])))
    # Comment replies are structurally threaded by id; resolve itself can be an asker mark.
    for e in events:
        a = e.get("args") or {}
        if e.get("verb") in ("comment", "resolve") and a.get("id"):
            replies.setdefault(a["id"], []).append(dict(root=e["id"], event=e, fields=a,
                                                        source=e["id"], resolved=e["verb"] == "resolve"))
    return roots, replies


def _question_reasons(w, events, news):
    roots, replies = _questions(w, events)
    for q in roots:
        root, e, fields = q["root"], q["event"], q["fields"]
        asker = persons.of_event(w, e) or ""
        exact = replies.get(root, [])
        kind = fields.get("request_kind", "")
        # An original asker can classify a legacy root, without editing history or reading prose.
        for reply in exact:
            if kind in ("question", "permission"):
                break
            if persons.of_event(w, reply["event"]) == asker and asker:
                typed = reply["fields"].get("request_kind") or reply["fields"].get("mark")
                if typed in ("question", "permission"):
                    kind = typed
        unknown_kind = kind not in ("question", "permission")
        kind = kind if not unknown_kind else "question"
        target = canonical(w, q["about"]) if q["about"] else root
        recipients = q["to"] if isinstance(q["to"], list) else re.split(r"[, ]+", q["to"])
        recipients = list(dict.fromkeys(person(w, x, e) for x in recipients if x)) or [""]
        for recipient in recipients:
            r = _reason(kind, root, q["source"], target or root, asker, recipient)
            r["request_key"] = f"ask-{root}"
            issues = []
            if unknown_kind:
                issues.append("request_kind is untyped; original asker must classify")
            if q["about"] and not target:
                issues.append("authored target is unknown")
            if not recipient:
                issues.append("recipient is unknown")
            if not asker:
                issues.append("original asker is unknown")
            if not unknown_kind:
                for reply in exact:
                    revent, f = reply["event"], reply["fields"]
                    actor = persons.of_event(w, revent)
                    act = f.get("resolution") or f.get("mark")
                    evidence = reply["source"]
                    if kind == "permission":
                        valid = ((act in ("accept", "decline") and actor == recipient and recipient)
                                 or (act == "withdraw" and actor == asker and asker))
                    else:
                        valid = bool(recipient and actor == recipient
                                     and (not reply.get("resolved") or f.get("line")))
                        if actor == asker and asker:
                            mark_evidence = f.get("resolution_evidence") or f.get("evidence")
                            valid = bool((act == "answered" and any(x["source"] == mark_evidence for x in exact))
                                         or (reply.get("resolved") and f.get("line")))
                    if valid:
                        r.update(resolution_state="resolved", resolution_evidence=evidence, eligible="no")
                        break
            if kind == "question" and (q["parent"] in news or target in news):
                r["eligible"] = "no"
            r["uncertainty"] = "; ".join(issues)
            yield r


def _native_reasons(w, events):
    by_id = {e["id"]: e for e in events}
    for sid, s in w.subjects.items():
        acts = (s.get("promise") or {}).get("acts") or []
        original = next((by_id[a[0]] for a in acts if a[1] == "ask" and a[0] in by_id), None)
        if not original:
            continue
        asker = persons.of_event(w, original) or ""
        # Creation args are historical; mutable props and today's name bearer are not the recipient.
        to = (original.get("args") or {}).get("to", "")
        recipient = person(w, to, original) if to else ""
        about = (original.get("args") or {}).get("about", "")
        target = canonical(w, about) if about else sid
        r = _reason("permission", sid, sid, target or sid, asker, recipient)
        issues = []
        if not asker:
            issues.append("original asker is unknown")
        if not recipient:
            issues.append("recipient is unknown")
        if about and not target:
            issues.append("authored target is unknown")
        for a in acts:
            e = by_id.get(a[0])
            if not e or int(e["id"][1:]) <= int(original["id"][1:]):
                continue
            actor, act = persons.of_event(w, e), a[1]
            if ((act in ("accept", "decline") and recipient and actor == recipient)
                    or (act == "withdraw" and asker and actor == asker)):
                r.update(resolution_state="resolved", resolution_evidence=e["id"], eligible="no")
                break
        r["uncertainty"] = "; ".join(issues)
        yield r


def _evaluate(desk, recipient, policy):
    w = desk.world
    _, policy_recipient, selections, labels, p = _policy(desk, policy)
    events = _active_events(w)
    reasons = []
    for kind in ("design", "review"):
        for target in sorted(selections["action_" + kind + "s"]):
            origin = _origin(w, target, events, p["action_" + kind + "s"])
            r = _reason(kind, f"{target}-{(origin or {}).get('id', 'unknown')}", target,
                        target, (persons.of_event(w, origin) or "") if origin else "", policy_recipient)
            r["label"] = labels[kind]
            if not r["asker"]:
                r["uncertainty"] = "original asker is unknown"
            if kind == "review" and target in selections["action_review_later"]:
                r["later"] = "yes"
            reasons.append(r)
    reasons.extend(_question_reasons(w, events, selections["action_question_news"]))
    reasons.extend(_native_reasons(w, events))
    grouped = {}
    for r in reasons:
        if r["recipient"] and r["recipient"] != recipient:
            continue
        # Unknown identities have their own diagnostic namespace, never become this person's duty.
        key = f"{r['recipient'] or 'unknown'}~{r['target']}"
        r["key"] = key
        r["item"] = r["source"]
        r["asker_label"] = persons.label(w, r["asker"]) if r["asker"] else "unknown"
        r["recipient_label"] = persons.label(w, r["recipient"]) if r["recipient"] else "unknown"
        if r["uncertainty"]:
            r["eligible"] = "no"
        grouped.setdefault(key, []).append(r)
    groups = []
    for key, members in sorted(grouped.items()):
        target = members[0]["target"]
        active = [r for r in members if r["eligible"] == "yes" and r["resolution_state"] == "open"]
        obj = w.subjects.get(target) or w.nodes.get(target) or {}
        groups.append(dict(key=key, target=target, item=target, title=obj.get("title") or target,
                           later="yes" if target in selections["action_group_later"] else "no",
                           reason_count=len(active), counted="yes" if active else "no",
                           recipient=members[0]["recipient"],
                           uncertainty="; ".join(sorted({r["uncertainty"] for r in members if r["uncertainty"]}))))
    return groups, grouped


def snapshot(desk, arg, reasons=False):
    import scene
    parts = arg.split(":")
    if len(parts) != (3 if reasons else 2) or any(not p for p in parts):
        raise Refusal("action-reasons:<recipient>:<policy>:<group-key>" if reasons else "actions:<recipient>:<policy>")
    recipient = person(desk.world, parts[0])
    if not recipient:
        raise Refusal("actions recipient must name a known person; there is no default")
    policy = canonical(desk.world, parts[1])
    groups, members = scene._once(desk.world, ("actions", recipient, policy),
                                  lambda: _evaluate(desk, recipient, policy))
    return [dict(r) for r in (members.get(parts[2], []) if reasons else groups)]
