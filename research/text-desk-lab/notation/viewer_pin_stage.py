"""Staged world-authored Viewer controls for Rowan; importing this applies nothing.

Arguments are viewer appearance and target lens appearance. Owner/kind checks live in world policy.
Reorder takes viewer, existing pin, existing anchor (before it). Removing then Pin restores at the end;
reorder or an explicit recorded inverse restores the original position.
"""
OWNER = '$1.role = "home-view" and $1.actor = $me'
# Preserve the existing Viewer's islens policy, including its ordinary `has` semantics.
LENS = '($2.kind = "lens" or ($2.kind = "note" and $2.tags has "lens"))'

VERBS = {
    "viewer-pin": (
        f'do prop $1 pins="$(refs-add(($1.pins or \\"\\"), $2))" '
        f'when {OWNER} and {LENS} and refs-add(($1.pins or ""), $2) != ($1.pins or "")'),
    "viewer-unpin": (
        f'do prop $1 pins="$(refs-remove(($1.pins or \\"\\"), $2))" '
        f'when {OWNER} and refs-remove(($1.pins or ""), $2) != ($1.pins or "")'),
    "viewer-pin-before": (
        f'do prop $1 pins="$(refs-before(($1.pins or \\"\\"), $2, $3))" '
        f'when {OWNER} and refs-before(($1.pins or ""), $2, $3) != ($1.pins or "")'),
}

# Exact additive anchors in the read a5486 text. Re-read before applying; never replace whole lens.
HUNKS = [
    ('  on click do prop $v viewing=$p back="$v.viewing" find="" with=""',
     '  on click do prop $v viewing=$p back="$v.viewing" find="" with=""\n'
     '  on menu "Unpin" when refs-remove(($v.pins or ""), $p) != ($v.pins or "") do viewer-unpin $v $p'),
    ('    pop : text "Pop out"',
     '    pin : text "Pin this lens"\n'
     '      role chip\n'
     '      only when islens = "yes" and refs-add(($v.pins or ""), $item) != ($v.pins or "")\n'
     '      on click do viewer-pin $v $item\n'
     '    pop : text "Pop out"'),
]


def patch(text, reverse=False):
    for old, new in reversed(HUNKS) if reverse else HUNKS:
        before, after = (new, old) if reverse else (old, new)
        if text.count(before) != 1:
            raise ValueError("Viewer pin patch anchor moved or is ambiguous")
        text = text.replace(before, after, 1)
    return text
