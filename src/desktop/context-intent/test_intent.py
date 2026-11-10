"""Exercise actual compiled composer gestures in a fresh in-memory fixture only.

No live world, Conversation, profile, browser, captures or model calls are used.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
sys.path[:0] = [str(HERE), str(LAB)]
import explore
import moo
import scene
import patches


def walk(n):
    yield n
    for k in n.get("kids", []):
        yield from walk(k)


d = explore.fresh()
d._session = "intent-inmemory"
d.world.me = "tester"
root = d.world.root


def act(line, refused=False):
    r = d.dispatch("desk", {"line": line})
    text = r.get("text") or str(r)
    bad = bool(r.get("error")) or text.startswith("ERR") or "\nERR" in text or "refused:" in text
    assert bad == refused, (line, text)
    return text


def make(kind, title, text="", **props):
    act(f"look {root}")
    kv = " ".join(k + "=" + patches.q(v) for k, v in props.items())
    got = act(f"do create {root} kind={kind} title={patches.q(title)} " +
              (f"text={patches.q(text)} " + kv if kind != "surface" else ""))
    nid = re.search(r"→ created ([af]\d+)", got).group(1)
    if kind == "surface":
        act(f"look {nid}")
        act(f"do prop {nid} {kv}")
    return nid


def prop(n, **values):
    act(f"read {n}")
    act(f"do prop {n} " + " ".join(k + "=" + patches.q(v) for k, v in values.items()))


def props(n):
    return moo.props_of(d.world, n)


for person in ("jeff", "pike", "sable", "tester"):
    make("surface", person + " fixture corner", role="resident", actor=person)
make("note", "reply", 'do comment $1 line="$*"', tags="verb", on="house")
chat = make("chat", "Fixture feed", members="all")
draft = make("note", "Fixture draft", "Unsent words stay intact", role="conversation-draft",
             actor="tester", to="jeff", view="all", context="")
doc = make("note", "Document One", "## Plan\nThe exact selected words.", author="pike")
other = make("note", "Document Two", "Unrelated.", author="sable")
view = make("note", "Fixture viewer", role="home-view", actor="tester", viewing=doc)
writer = make("note", "Fixture writer", role="writer", actor="tester", view="conversation",
              open=doc, quote="", quote_in="", quoting="")
texts = {name: patches.apply(name, patches.before(name))
         for name in ("jeff-chat", "conversation")}
roles = sorted({m for text in texts.values() for m in re.findall(r"^\s+role ([\w.]+)", text, re.M)})
skin = (LAB / "desk-shell/style/calm.style").read_text(encoding="utf-8")
skin += "\n" + "\n".join("role " + r + " : text" for r in roles)
make("note", "intent-style", skin, tags="style")
make("note", "home-usage", "quota : column\n", tags="lens", style="intent-style")
for name, text in texts.items():
    # Fixture ids replace only the live destinations; fixture writes never
    # reach the shared Conversation and the test never reads its stored lines.
    text = text.replace("a5080", chat).replace("f3402", root).replace("involving:alex", "involving:tester")
    make("note", name, text, tags="lens", style="intent-style")


def nodes(lens="jeff-chat"):
    sc, _ = scene.scene_for(d, lens)
    return [n for n in walk(sc) if not n.get("paint", {}).get("absent")]


def gesture(part, on="click", value=None, lens="jeff-chat", refused=False, contains=None):
    found = [n for n in nodes(lens) if n.get("part") == part and n.get("acts")]
    if part == "say":
        found = [n for n in found if ("/commenting/" in n["key"]) == bool(props(writer).get("quote"))]
    if contains:
        found = [n for n in found if any(contains in a["line"] for a in n["acts"])]
    assert len(found) == 1, [(n["key"], n.get("acts")) for n in found]
    acts = [a for a in found[0]["acts"] if a.get("on", "click") == on]
    assert len(acts) == 1, acts
    line = acts[0]["line"]
    if value is not None:
        line = line.replace("$value", value)
    return act(line, refused=refused)


def lines(where=chat):
    return d.world.subjects[d.world.subject_of(where)]["lines"]


def fields(line):
    return scene.line_fields(line)


def has_chip(lens="jeff-chat"):
    return any(n.get("part") == "lifetime" for n in nodes(lens))


# Ordinary navigation and repaints must never manufacture a topic.
initial = dict(props(draft))
nodes()
prop(view, viewing=other)
nodes()
assert props(draft) == initial
gesture("say", "edit", "Plain while a document is open")
assert not fields(lines()[-1]).get("about")
assert not has_chip()
print("ok: navigation/repaint preserve draft; plain send with document open has no about")

# An explicit attach names precisely the document at the press, not future view.
gesture("attach")
assert props(draft)["topic"] == other and has_chip()
assert has_chip("conversation"), "shared draft context must also be visible in the native composer"
prop(view, viewing=doc)
assert props(draft)["topic"] == other and has_chip()
gesture("say", "edit", "An intentionally attached item")
assert fields(lines()[-1])["about"] == other
assert not props(draft).get("topic") and not has_chip()
gesture("say", "edit", "Unrelated followup")
assert not fields(lines()[-1]).get("about")
print("ok: explicit attach survives navigation, sends exact item once; unrelated followup is plain")

gesture("attach")
gesture("remove")
assert not props(draft).get("topic") and not has_chip()
gesture("say", "edit", "Removed before send")
assert not fields(lines()[-1]).get("about")
print("ok: chip removal prevents context on send")

# A rejected send leaves its visible intent available; no false consumption.
gesture("attach")
prop(draft, to="unknown-fixture-recipient")
old_count = len(lines())
gesture("say", "edit", "Refuse this fixture send", refused=True)
assert len(lines()) == old_count and props(draft)["topic"] == doc and has_chip()
prop(draft, to="jeff")
gesture("say", "edit", "Retry exactly once")
assert fields(lines()[-1])["about"] == doc and not props(draft).get("topic")
print("ok: refused send retains its chip; successful retry consumes it")

# Inline/native main composer reads the same explicit intent, and consumes it.
gesture("attach")
gesture("say", "edit", "Native composer with explicit context", lens="conversation")
assert fields(lines()[-1])["about"] == doc
assert not has_chip() and not has_chip("conversation")
gesture("say", "edit", "Native unrelated followup", lens="conversation")
assert not fields(lines()[-1]).get("about")
print("ok: native composer exposes and consumes the same one-message topic")

# Replying is intentional discussion; no viewer-derived metadata is needed.
act(f'do append {chat} line="An actual document question" to=tester about={doc}')
question = lines()[-1]
prop(view, viewing=other)
gesture("attach")
gesture("answer", contains=question["id"])
assert not props(draft).get("topic"), "Answer supersedes an unrelated pending topic"
gesture("say", "edit", "Answer the actual document question")
answer = lines()[-1]
rows = {r["saying"]: r for r in scene.rows(d, "sayings involving:tester")}
assert answer["reply_to"] == question["id"]
assert rows[answer["id"]]["about"] == doc
assert not props(draft).get("reply_to")
gesture("say", "edit", "Unrelated after answering")
assert not lines()[-1].get("reply_to") and not fields(lines()[-1]).get("about")
prop(draft, reply_to=question["id"], quote="An actual document question", reply_in=chat)
gesture("say", "edit", "Native answer to actual question", lens="conversation")
assert lines()[-1]["reply_to"] == question["id"] and not props(draft).get("reply_to")
gesture("say", "edit", "Native unrelated after answering", lens="conversation")
assert not lines()[-1].get("reply_to") and not fields(lines()[-1]).get("about")
print("ok: HUD/native explicit replies retain real thread context; later sends do not inherit it")

# Selection/comment wins over an unrelated explicit attachment, and remains
# anchored to the document's actual paragraph and Talk, irrespective of viewer.
talk = make("chat", "Fixture document Talk", talk_of=doc, with_="tester,pike", members="all")
prop(doc, talk=talk)
assert props(view)["viewing"] == other
prop(draft, topic=other)
prop(writer, quote="The exact selected words.", quote_in=doc, quoting=doc, open=doc)
assert not has_chip()
gesture("say", "edit", "A true selected-text comment")
comment = lines(talk)[-1]
assert fields(comment)["about"] == doc and fields(comment)["quote"] == "The exact selected words."
assert not props(writer).get("quote") and not props(draft).get("topic")
gesture("say", "edit", "Unrelated after comment")
assert not fields(lines()[-1]).get("about")
prop(writer, quote="The exact selected words.", quote_in=doc, quoting=doc)
gesture("say", "edit", "Selected comment without pending topic")
assert fields(lines(talk)[-1])["about"] == doc and not props(writer).get("quote")

# The create-Talk branch must preserve a selection even without other intent.
prop(writer, quote="Unrelated.", quote_in=other, quoting=other, open=other)
gesture("say", "edit", "First actual comment on Document Two")
new_talk = props(other)["talk"]
assert fields(lines(new_talk)[-1])["about"] == other
assert fields(lines(new_talk)[-1])["quote"] == "Unrelated."

# A reply begun in the HUD and finished in native keeps its actual destination.
prop(draft, reply_to=comment["id"], quote="A true selected-text comment", reply_in=talk)
gesture("say", "edit", "Native reply on document Talk", lens="conversation")
assert lines(talk)[-1]["reply_to"] == comment["id"] and not props(draft).get("reply_to")
gesture("say", "edit", "Plain after native Talk reply", lens="conversation")
assert not fields(lines()[-1]).get("about")
assert d.world.subjects[d.world.subject_of(draft)]["text"] == "Unsent words stay intact"
print("ok: existing/new Talk selection comments keep true document/quote; native Talk reply stays there")
print("ok: unrelated sends stay plain; stored draft words untouched")
print("all ok: in-memory compiled gestures only; browser/input delivery not verified")
