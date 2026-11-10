"""copy_check.py (a8911): desk lines that apply the staged question routing to a COPY and exercise it.

    python src/desktop/notice-routing/copy_check.py <out-dir>
writes stage.desk (as jeff: the verb note beside the rule, the rule pointed at it) and ask.desk (as a worker
and the house: a question on a JEFF-asked card and on an Alex-asked one, an explicit question to Alex, then
commission=waiting on each). Run them with explore.py on a -try copy only, never the live world.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULE, HOME = "a5701", "f5204"
OLD = 'when prop:commission=waiting do create "Alex\'s notices" kind=note title=asking role=notice to=alex topic=asking about=$item came=$now'
NEW = "when prop:commission=waiting do notify-question-owner $item"


def q(v):
    return json.dumps(v, ensure_ascii=False)


def stage():
    verb = (HERE / "notify-question-owner.verb").read_text(encoding="utf-8").rstrip("\n")
    return [f"look {HOME} :1",
            f"do create {HOME} kind=note title=notify-question-owner tags=verb on=house text={q(verb)}",
            f"read {RULE}",
            f"do replace {RULE} old={q(OLD)} new={q(NEW)}"]


def asks(jeff_card, alex_card, perm_card):
    return {"worker": [f"look {jeff_card} :1", f'do comment {jeff_card} line="Copy check: which way, A or B?" mark=ask',
                       f"look {alex_card} :1", f'do comment {alex_card} line="Copy check: may I go on?" mark=ask',
                       f"look {perm_card} :1",
                       f'do comment {perm_card} line="Copy check: Alex, may this program be ended?" to=alex mark=ask'],
            "house": [f"look {c} :1\ndo prop {c} commission=waiting" for c in (jeff_card, alex_card, perm_card)]}


if __name__ == "__main__":
    out = Path(sys.argv[1])
    (out / "stage.desk").write_text("\n".join(stage()) + "\n", encoding="utf-8")
    a = asks(*sys.argv[2:5])
    (out / "ask-worker.desk").write_text("\n".join(a["worker"]) + "\n", encoding="utf-8")
    (out / "ask-house.desk").write_text("\n".join(a["house"]) + "\n", encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(out.glob("*.desk"))))
