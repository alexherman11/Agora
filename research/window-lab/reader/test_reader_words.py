"""test_reader_words.py: the words the reader (a6460) reads a document with: for-alex(), lead(), read-minutes().

    python research/window-lab/reader/test_reader_words.py

Real shapes, not made-up ones: the collaboration report's opening (a byline and a legend, then headings and lists, no
prose paragraph before its lists), a JEFF proposal with the For Alex block written each way the Handbook allows, a
commission card (What: ... Why: ...), and a design document with no block at all.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"))
import expr as X  # noqa: E402

FAILS = []


def call(name, *args):
    return X.call(name, [X.typed(a) for a in args])


def check(what, got, want):
    ok = got == want
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f": got {got!r}, want {want!r}"))
    if not ok:
        FAILS.append(what)


def val(v):
    return None if v.is_none() else X.fmt(v)


REPORT = """worker-a5251 for JEFF, 15 Oct. [read] = read in the world or code; [ran] = a query I ran today. Nothing changed.

## 1. Collaboration
Working:
- Disagreement is written separately and kept: Pike's a4205 took Sable's cases. [read]
- Corrections are public. [read]

## 2. What blocks many workers
1. Two slots: workers=2 (a566); workshop.py:279 counts a card as running while it is working. [read]
"""

HEADED = """## For Alex
What: a reader for everything that waits on you, with answers in one press.
I recommend: build it now; it replaces the review viewer.
I need: yes or no on making it open by default.

## Why
The waiting list is a wall of links today. Each reference is a long underlined name.
"""

BOLD = """**For Alex**
- **What:** the bar's icons, names on hover.
- **I recommend:** keep it.
> **I need:** nothing: just so you know.

The bar now sits at the bottom. Apps and widgets together."""

CARD = "What: Alex (17 Oct 10:18), with a screenshot: 'queue: I need some better way'. Why: Alex's daily reading."

DESIGN = """# Where visitors stand

A visitor stands in one place at a time, and the desk says where. This is the one choice left.

## The choice
- One room or many."""


def main():
    check("For Alex under a heading: what", val(call("for-alex", HEADED, "what")), "a reader for everything that waits on you, with answers in one press.")
    check("For Alex under a heading: recommend", val(call("for-alex", HEADED, "recommend")), "build it now; it replaces the review viewer.")
    check("For Alex under a heading: need", val(call("for-alex", HEADED, "need")), "yes or no on making it open by default.")
    check("rest drops the block, keeps the rest", val(call("for-alex", HEADED, "rest")).startswith("## Why"), True)
    check("For Alex as a bold line with a list and a quote: what", val(call("for-alex", BOLD, "what")), "the bar's icons, names on hover.")
    check("bold keys: need", val(call("for-alex", BOLD, "need")), "nothing: just so you know.")
    check("bold block: rest is the prose", val(call("for-alex", BOLD, "rest")), "The bar now sits at the bottom. Apps and widgets together.")
    check("no block: none", val(call("for-alex", REPORT, "what")), None)
    check("no block: rest is the whole text", val(call("for-alex", REPORT, "rest")).strip(), REPORT.strip())
    check("a wrong key is none", val(call("for-alex", HEADED, "why")), None)
    check("lead skips the block and the heading", val(call("lead", HEADED)), "The waiting list is a wall of links today.")
    check("lead after a bold block", val(call("lead", BOLD)), "The bar now sits at the bottom.")
    check("lead of a design: its first sentence past the title", val(call("lead", DESIGN)), "A visitor stands in one place at a time, and the desk says where.")
    check("lead of the report: a byline with a legend and lists only is none", val(call("lead", REPORT)), None)
    check("lead never reaches past the opening section", val(call("lead", "Intro:\n- a list\n\n## Three\nSource read: a long sentence of prose here.")), None)
    check("lead of a card: its first sentence", val(call("lead", CARD)), "What: Alex (17 Oct 10:18), with a screenshot: 'queue: I need some better way'.")
    check("lead of a long sentence is cut at a word", (val(call("lead", "word " * 80 + "end.")) or "").endswith("…"), True)
    check("gist of a section that is only a list: its first item", val(call("gist", "Working:\n- Disagreement is written separately and kept: Pike's a4205 took it. [read]\n- More.")),
          "Disagreement is written separately and kept: Pike's a4205 took it.")
    check("gist of a numbered list", val(call("gist", "1. Two slots: workers=2 (a566); it counts a card. [read]")), "Two slots: workers=2 (a566); it counts a card.")
    check("read-minutes: a short note is a minute", val(call("read-minutes", HEADED)), "1")
    check("read-minutes: 900 words", val(call("read-minutes", "w " * 900)), "4")
    print("reader words:", "ok" if not FAILS else f"{len(FAILS)} FAIL")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
