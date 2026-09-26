#!/bin/bash
# Sable, 26 Sep 2026. The runs to make after the quiet-window patches land, in order, from Git Bash.
# Apply (deskd stopped; nothing else running that imports the lab's Python):
#   cd C:/Projects/Agora4
#   git apply research/object-facet-frontier/experiments/patches/1-chat-signed-by-writer.patch   # world.py
#   git apply research/object-facet-frontier/experiments/patches/2-sable9-switch.patch           # world.py, needs 1's file state only by context; applies alone too
#   git apply research/object-facet-frontier/experiments/patches/3-box-reads.patch               # knife.py, moo.py: needs 2 (world.box)
# Every patch was checked with `git apply --check` against main 538cfd8; applying 1+2+3 to copies of main's files
# reproduces byte-for-byte the world.py these numbers were measured on.
#
# Expected (ran, in a scratch copy of 538cfd8 with the three patches; OFF = DESK_GEOMETRY unset, ON = choices):
#   test_scene                      19 passed, OFF and ON
#   test_journal                    OFF: 9 breaks, 1 half, 1 hidden, 1 holds, 7 journal (unchanged from main)
#                                   ON:  8 breaks, 2 half, 1 hidden, 1 holds, 7 journal: S12 goes breaks -> half
#                                        (0 sibling rows clash, was 4 on geom:pos; the 2 left are the fresh-id collision a14/s13)
#   suite trip/workspace/budget/blocks/reads/host/attacks   identical to main OFF and ON (only the world.py hash line moves);
#                                   goldens: trip 3 same, budget 1 same, blocks 2 same
#                                   (trip's and budget's recorded-run lines already differ on main 538cfd8: trip M4 2/1/1 -> 0,
#                                   budget M3 16 -> 23; the patches leave them as main has them)
#   suite chat                      M4 2 -> 0 ("against the recorded run: M4 2 then, 0 now"): rebless chat's recorded run
#   golden_prints (46 lenses, 16 sessions)   identical to main, OFF and ON
#   soundness                       UNSOUND 0 in all 13 cases (juniper-7 900 trials, today 58, tracks 116, probes 48), OFF and ON
#   working_copy                    OFF as main; ON: rows per act create 31->9, move 23->2, resize 21->1, remove 25->5,
#                                   tidy 23->1, tag (rule r2 moves) 24->4; all 17 acts rebuild from rows and from nothing
#   layout9                         OFF: 3 of 60 acts drift 1px on a second reflow; ON: 0
#   boxprobe                        the same JSON before and after patch 3, OFF and ON
set -e
PY=C:/Projects/Agora4/.venv/Scripts/python.exe
N=C:/Projects/Agora4/research/text-desk-lab/notation
X=C:/Projects/Agora4/research/object-facet-frontier/experiments
for G in "" choices; do
  export DESK_GEOMETRY=$G
  echo "======== DESK_GEOMETRY=${G:-off}"
  cd $N
  $PY -m pytest -q test_scene.py | tail -1
  $PY test_journal.py | grep -E "^S12|^tally"
  for c in trip workspace budget chat blocks reads host attacks; do
    $PY suite/run.py $c | grep -E "against the recorded run|golden prints" | sed "s/^/$c: /"
  done
  $PY golden_prints.py /tmp/golden-${G:-off} | tail -1
  cd $X
  $PY soundness/soundness.py | grep UNSOUND
  $PY journal/working_copy.py | grep -E "^- (create|tag|move|resize|remove|tidy)" | cut -c1-160
  $PY geometry/layout9.py | grep "second reflow"
  $PY patches/boxprobe.py $N
done
unset DESK_GEOMETRY
diff -r /tmp/golden-off /tmp/golden-choices && echo "golden prints: switch off and on identical"
# then a CLI smoke test in a private session (not frontier):
#   printf 'run arrive\nlook\n' | $PY $N/explore.py frontier-sable --as sable
