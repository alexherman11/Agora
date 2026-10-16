"""houseverbs: the verbs of the house that used to be Python (9 Oct 2026, step 6 of the grammar unification).

Until a990 the desk had a specialized tier of built-in verbs composed from the primitives in moo.py (tidy, split,
gather, reveal, dedupe, done, stack, and reply); a990 retired them from the desk, which refused each with an
alternative (`no tidy here; use tile`) while letting a world verb answer the word. On 9 Oct their Python left moo.py
and the words became verb notes of the house, written in the desk's own language and read by verbs.py like any verb a
person makes: `help tidy` describes the note, `examine` names it at hand, a room's own tidy stands over it, and anyone
may rewrite it. This module holds the seed texts so the live world and the test worlds (roomworld.build(house=True))
agree; the world's copy is the living one.

What could not move, and why: `split` (two groups by a rule) and `stack` (an offset per child) need a step for each
child of a surface, and a verb note has no `for each`; the Writing room already owns a `split` of its own (a3571).
`tidy`'s `as=row` and `gather`'s several words wait on an optional blank (`$2` refuses when the word is missing), and
`reply` cannot take the caller's `line=` as the built-in did: `$*` arrives as one quoted word, so a note passes no k=v
through; its words are its second word instead (`reply <chat> "<words>"`).
"""

NOTES = (
    ("tidy", "# tidy <surface>: make nothing overlap: tile it as a column, in its current order\n"
             "# (a built-in until 9 Oct 2026; now this note. For a row: do tile <surface> as=row)\n"
             "do tile $1 as=column"),
    ("gather", "# gather <surface> <word>: bring every thing whose title, text or tags hold the word into the surface,\n"
               "# one appearance per thing (a built-in until 9 Oct 2026; now this note)\n"
               "do move ?$2 into=$1 one=1"),
    ("dedupe", "# dedupe <appearance>: keep this appearance and remove every other appearance of its subject\n"
               "# (a built-in until 9 Oct 2026; now this note)\n"
               "do remove also:$1"),
    ("reveal", "# reveal <appearance>: bring it to the front of its surface (a built-in until 9 Oct 2026; now this note)\n"
               "do raise $1"),
    ("done", "# done <card>: mark the task done: its card goes to the bottom of the done lane (status=done, the house's\n"
             "# ranks, one event). A built-in until 9 Oct 2026, when it prefixed the title with a check; now this note\n"
             "do put $1 status=done"),
    ("reply", "# reply <chat> \"<words>\": add a line to a chat. It is append by another name (a built-in word until\n"
              "# 9 Oct 2026; now this note). A verb note cannot pass line=... through, so the words are its second word\n"
              "do append $1 line=\"$2\""),
    # 9 Oct (a3806; Pike, Juniper and Sable, m3799 on): until now the word lived in Pike's corner and wrote to one
    # chat by id; friction went unwritten because writing it cost a room, a family and a status. The chat is found by
    # its role, so the note is the same in every world
    ("wish", "# wish <words>: say that something hurt, was missing, or cost you, from anywhere, in one line.\n"
             "# It lands in the chat whose prop role=wishes. Your last line the desk did not do, and what the desk\n"
             "# said back, are added for you ($reach), so there is nothing to copy. No family, no status, and no\n"
             "# deciding whose fault it was: someone sorts later (rows reaches counts what the desk refused).\n"
             "do append prop:role=wishes line=\"$* $reach\""),
    # 16 Oct (a5824; Alex wants to be told when work finishes): the line is the record (who and when are its event), and
    # the house turns each new one into a Windows toast on his PC (house.toasts, research/window-lab/notify.py)
    ("notify", "# notify <words>: tell Alex, as a Windows notification on his PC (title Agora, silent; words that begin\n"
               "# with ! ring). Each send is a line in the chat with prop role=notifications (Notifications sent): who,\n"
               "# when and the words, so none is silent. The house shows it within seconds while it runs the live world;\n"
               "# Focus Assist or Do not disturb hold the banner back (it waits in his notification centre)\n"
               "do append prop:role=notifications line=\"$*\""),
)


def lines(surface):
    """The desk lines that make the notes on `surface`, as the house's verbs (on=house)."""
    out = []
    for word, text in NOTES:
        body = text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n")
        out.append(f'do create {surface} kind=note title={word} tags=verb on=house text="{body}"')
    return out
