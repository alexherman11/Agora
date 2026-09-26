"""Comment over-fence probe (Sable, 26 Sep). Run from research/text-desk-lab/notation: python <this file>. Alex reads a note with
comments c04 (his) and c05 (Ben's); Ben does one act; Alex resolves c04. ran on main be8181c, output in comment_overfence.txt."""
import sys, re
sys.path.insert(0, ".")
import test_journal as T
def run(ben_act):
    dk = T.Desk()
    dk.do("look")
    note = T.made(dk.do('do create f01 kind=note title="House rules" text="quiet after ten"'))
    sid = dk.w.nodes[note]["subject"]
    dk.do(f'do comment {note} line="ten is early"')
    dk.do("look", "ben"); dk.do(f"read {note}", "ben")
    dk.do(f'do comment {note} line="what about weekends"', "ben")
    cids = [c["id"] for c in dk.w.subjects[sid]["comments"]]
    dk.do(f"read {note}"); dk.do(f"read {note}", "ben")
    b = dk.do(ben_act.format(note=note, c1=cids[0], c2=cids[1]), "ben")
    a = dk.do(f'do resolve {note} id={cids[0]} line="fine, eleven"')
    st = dk.w.subjects[sid]["comments"]
    return T.first(b), " | ".join(a.splitlines()) + f"\n  after: {[(c['id'], c['resolved']) for c in st]}"
for label, act in [("ben comments anew", 'do comment {note} line="and guests?"'),
                   ("ben resolves the other comment", 'do resolve {note} id={c2}'),
                   ("ben appends to the text", 'do append {note} line="no drums"'),
                   ("ben resolves the same comment (true conflict)", 'do resolve {note} id={c1} line="ok"')]:
    b, a = run(act)
    print(f"{label}:\n  ben:  {b}\n  alex resolve c1: {a}")
