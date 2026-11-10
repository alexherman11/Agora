"""World definitions for delegated handoff refusal notices.

Generate authorised Lines; no session, credentials, network or activation here.
The installer passes the actual chat/policy IDs returned by its own session.
"""
import json


def line(word, **facts):
    return word + " " + " ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in facts.items())


def policy_line(chat):
    return line("make", kind="handoff-policy", name="Delegated handoff refusal matching", chat=chat,
                scope=r"\b(?:my|this session|its governing|the governing).{0,100}(?:scope|instructions)"
                      r".{0,100}(?:exclud|limit|only|restrict)|\bscope[- ]limited\b",
                provider=r"\b(?:i(?:'ve|’ve| have)|you(?:'ve|’ve| have)) hit (?:your |my |the )?"
                         r"(?:session|usage|provider) limit\b|"
                         r"\bmy (?:provider|session|usage|rate) (?:limit|quota) (?:is |has been )?"
                         r"(?:exhausted|reached|exceeded|blocked)\b",
                cannot=r"\bi (?:can(?:not|'t|’t)|am unable to) (?:accept|take|resume|brief|start|pick up|work on)\b",
                session=r"\b(?:this session|my session|my governing|its governing).{0,140}(?:scope|instructions)"
                        r".{0,80}(?:exclud|limit|only|restrict)|"
                        r"\b(?:i(?:'ve|’ve| have)|you(?:'ve|’ve| have)) hit (?:your |my |the )?"
                        r"(?:session|usage|provider) limit\b|"
                        r"\bmy (?:provider|session|usage|rate) (?:limit|quota) (?:is |has been )?"
                        r"(?:exhausted|reached|exceeded|blocked)\b",
                resolved=r"\b(?:no longer|not) (?:scope-limited|blocked|limited)\b|"
                         r"\b(?:scope|instructions).{0,25}(?:does not|doesn't|do not|don't) (?:exclude|restrict)\b|"
                         r"\b(?:scope|instructions).{0,25}(?:now allows|now includes)\b")


def rule_lines(policy, off="yes", cc="Alex"):
    """Create disabled; hidden verification must precede explicit set off=no."""
    specs = [
        ("Record pending delegated handoffs", "house.hand", None,
         "handoff.open $target to_field=who owner=$by"),
        ("Recognize pending recipient refusals", "say", None,
         f"handoff.observe $said policy={policy}"),
        ("Wake delegator when a pending handoff is refused", "make", "handoff-refusal",
         'handoff.notify $target text="Handoff blocked: {task}; recipient {recipient}. {reason} — {source}"'
         + (f" cc={json.dumps(cc)}" if cc else "")),
        ("Accept handoff when recipient instructs worker", "house.tell", None,
         "handoff.close $target recipient=$by"),
    ]
    return [line("rule", name=name, on=on, by="anyone", off=off, do=action,
                 **({"kind": kind} if kind else {})) for name, on, kind, action in specs]
