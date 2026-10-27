# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_verb_tail (a894, a11657): ${N...} in a verb, the words from the Nth on.

    python test_verb_tail.py

A fresh world in memory (explore.fresh). ${N...} gives exactly the values $N, $N+1 ... give, one space between, so a
quoted reason and an unquoted one store the same words. It needs N words, counts from 1, is a value (filled once, never
read again as desk words, so quotes, backslashes and semicolons inside it cannot leave the value or run a command),
keeps literal dollars, stays as written in a typed line, and needs its braces: $1* is $1 then a Markdown star, and $*
is unchanged.
"""
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import explore  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1200]}"))
    if not ok:
        fails.append(name)


D = explore.fresh()
D._session = "verbtail-inmemory"
W = D.world
W.me = "pike"
ROOT = W.root


def reply(*lines):
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append(r.get("text") or ("ERR " + str(r.get("error"))))
    return out


def made(text):
    return re.search(r"created ([af]\d+)", text).group(1)


def stored(text):
    """A verb's lines as a do create text= value: its backslashes and quotes escaped once."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def verb(title, body):
    out = reply(f"look {ROOT}", f'do create {ROOT} kind=note title={title} tags=verb text="{stored(body)}"')
    check(f"the verb {title} is made", "created" in out[-1], out[-1])
    return made(out[-1])


def props(ident):
    return dict(W.subjects[W.nodes[ident]["subject"]].get("props") or {})


N = made(reply(f"look {ROOT}", f"do create {ROOT} kind=note title=Target")[-1])
OTHER = made(reply(f"look {ROOT}", f"do create {ROOT} kind=note title=Other")[-1])
verb("keep", 'do prop $1 kept="<${2...}>"')


def keep(words):
    out = reply(f"look {N}", f"keep {N} {words}")
    return out[-1], props(N).get("kept")


# the words, quoted or not
said, got = keep("fixed the timer")
check("unquoted words after the target are the tail", got == "<fixed the timer>", (got, said))
said, got = keep('"fixed the timer"')
check("a quoted reason gives the same words", got == "<fixed the timer>", (got, said))
said, got = keep("\"a b\" c 'd e'")
check("mixed quoting: the words as the line split them, one space between", got == "<a b c d e>", (got, said))
said, got = keep("one   two")
check("runs of spaces become one", got == "<one two>", (got, said))
said, got = keep('""')
check('an explicit "" is an empty tail', got == "<>", (got, said))
said, got = keep("café 🎉 漢字")
check("Unicode passes through", got == "<café 🎉 漢字>", (got, said))

before = props(N).get("kept")
said, got = keep("")
check("missing words refuse as $N does, and change nothing", said.startswith("ERR") and "needs 2 word(s)" in said
      and got == before, (said, got))

# literal dollars and one pass
said, got = keep(r"costs \$5")
check(r"\$5 is a literal dollar", got == "<costs $5>", (got, said))
said, got = keep("costs $5")
check("a typed $5 is a price, not a blank", got == "<costs $5>", (got, said))
said, got = keep(r"\$here \$1 \${2...} \$new")
check("dollars in the words are never filled again (one pass)", got == "<$here $1 ${2...} $new>", (got, said))
said, got = keep("$me said so")
check("a whole-word blank is filled where it was said, as $2 would be", got == "<pike said so>", (got, said))

# the value cannot leave its destination
n_events = len(W.events)
said, got = keep(f'"a; do remove {OTHER}"')
check("a quoted semicolon stays in the value and runs nothing", got == f"<a; do remove {OTHER}>"
      and OTHER in W.nodes and not W.nodes[OTHER].get("removed"), (got, said))
check("one use made one prop event", len([e for e in W.events[n_events:] if e["verb"] == "prop"]) == 1,
      [e["verb"] for e in W.events[n_events:]])
said, got = keep('\'say "hi" \\ there\'')
check("embedded quotes and a backslash stay inside the value", got == '<say "hi" \\ there>', (got, said))
said, got = keep("'x\" other=1 kept=evil'")
check("a quote and k=v words inside the tail make no other prop", got == '<x" other=1 kept=evil>'
      and "other" not in props(N), (props(N), said))
n_events = len(W.events)
out = reply(f"look {N}", f"keep {N} a; do remove {OTHER}")
check("an unquoted semicolon in a line to a verb is one of its words (as with $*): stored, never run",
      props(N).get("kept") == f"<a; do remove {OTHER}>" and not W.nodes[OTHER].get("removed")
      and [e["verb"] for e in W.events[n_events:]] == ["prop"], (props(N).get("kept"), [e["verb"] for e in W.events[n_events:]]))

# receipts and undo
prev = props(N).get("kept")
said, got = keep("shown in the receipt")
check("the receipt shows the filled tail", "shown in the receipt" in said, said)
ev = re.search(r"\[(e\d+)\]", said).group(1)
reply(f"look {N}", f"undo {ev}")
check("undo takes the use back", props(N).get("kept") == prev, (props(N).get("kept"), prev))

# typed lines, Markdown, bare forms, $* and zero
reply(f"look {N}", f"do prop {N} typed=${{3...}}")
check("in a typed line ${3...} stays as written", props(N).get("typed") == "${3...}", props(N).get("typed"))
verb("wave", 'do prop $1 said="*waves at $2*"')
reply(f"look {N}", f"wave {N} sable")
check("Markdown after a blank is unchanged: *waves at $2*", props(N).get("said") == "*waves at sable*", props(N).get("said"))
verb("bare", 'do prop $1 bare="$2*"')
reply(f"look {N}", f"bare {N} a b")
check("a bare $2* is $2 then a star", props(N).get("bare") == "a*", props(N).get("bare"))
verb("whole", 'do prop $1 whole="$*"')
reply(f"look {N}", f"whole {N} a  b")
check("$* is unchanged: the rest of the line exactly, target included", props(N).get("whole") == f"{N} a  b", props(N).get("whole"))
verb("all", 'do prop $1 all="${1...}"')
reply(f"look {N}", f"all {N} x")
check("${1...} is every word", props(N).get("all") == f"{N} x", props(N).get("all"))
verb("zero", 'do prop $1 zero="${0...}"')
out = reply(f"look {N}", f"zero {N} x")
check("${0...} refuses: words count from 1", out[-1].startswith("ERR") and "count from 1" in out[-1]
      and "zero" not in props(N), out[-1])
verb("far", 'do prop $1 far="${9...}"')
out = reply(f"look {N}", f"far {N} x")
check("past the last word refuses with the $N message", out[-1].startswith("ERR") and "needs 9 word(s)" in out[-1], out[-1])

# a rule has no words after a verb: its ${2...} is caught at save, as $2 is
out = reply(f"look {ROOT}", f'do create {ROOT} kind=note tags=rule title=probe text="when tag:probe do prop $item why=${{2...}}"')
check("a rule saying ${2...} is told it is a verb's word", "is a verb's word" in out[-1], out[-1])

# a tell-shaped publisher (a draft, not public tell)
verb("tellx", 'do prop $2 to=$1 why="${3...}"')
reply(f"look {N}", f"tellx mica {N} Synthetic completion fixture")
check("tell-shaped: why is the reason alone, not recipient and target", props(N).get("why") == "Synthetic completion fixture"
      and props(N).get("to") == "mica", props(N))
reply(f"look {N}", f'tellx mica {N} "Synthetic timer fixture"')
check("tell-shaped, quoted reason: the same shape", props(N).get("why") == "Synthetic timer fixture", props(N))
long = " ".join(f"w{i}" for i in range(40))
reply(f"look {N}", f"tellx mica {N} {long}")
check("a long reason is kept whole (words-after kept six)", props(N).get("why") == long, props(N).get("why"))

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
