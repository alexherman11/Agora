"""Generate ordinary staged world verbs; no world or host access."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def value(expression):
    # The command tokenizer consumes one quote layer before computation.
    return '"$(' + expression.replace('"', '\\"') + ')"'


def optional(field, default=""):
    return value(f'($1.{field} or "{default}")')


def build():
    is_panel = '($1.role or "") = "home-panel"'
    is_lens = '($1.kind = "lens" or ($1.tags or "") has "lens")'
    subject_expr = '($1.opens or $1.shows or $1.id)'
    subject = value(subject_expr)
    shared = ' '.join(f'{k}={optional(k, d)}' for k, d in
                      [('glyph', '◆'), ('icon', ''), ('tint', 'blue'), ('about', '')])
    policy = ' '.join(f'{k}={optional(k)}' for k in ('filled', 'chrome', 'sizing', 'pin'))
    pin = [
        '# dock-pin <thing> <dock>: stable descriptors, duplicate drops are no-ops.',
        f'do create $2 kind=note title="$1.title" role=dock-pin opens={subject} {shared} window={optional("window")} when not ({is_panel}) and not {is_lens} and (($1.window or "") = "" or ($1.opens or "") != "") and count(in:$2,prop:opens=$({subject_expr})) = 0 and count(in:$2,prop:opens=$1) = 0',
        f'do create $2 kind=note title="$1.title" role=dock-pin opens="" window=$1.window {shared} when not ({is_panel}) and not {is_lens} and ($1.window or "") != "" and ($1.opens or "") = "" and count(in:$2,prop:window=$1.window,-prop:opens) = 0',
        f'do create $2 kind=note title="$1.title" role=dock-pin lens=$1.lens shows={optional("shows")} {shared} {policy} when {is_panel} and ($1.shows or "") = "" and count(in:$2,prop:lens=$1.lens,-prop:shows) = 0',
        f'do create $2 kind=note title="$1.title" role=dock-pin lens=$1.lens shows=$1.shows {shared} {policy} when {is_panel} and ($1.shows or "") != "" and count(in:$2,prop:lens=$1.lens,prop:shows=$1.shows) = 0',
        f'do create $2 kind=note title="$1.title" role=dock-pin lens=$1.title shows="" {shared} when {is_lens} and count(in:$2,prop:lens=$1.title,-prop:shows) = 0',
    ]
    # Soft removal is reversible from the bar menu or by dropping the same
    # target again. Re-pin restores the original order instead of duplicating.
    for guard, selection in [
        ('true', f'in:$2,prop:opens=$({subject_expr})'),
        ('true', 'in:$2,prop:opens=$1'),
        ('($1.window or "") != ""', 'in:$2,prop:window=$1.window,-prop:opens'),
        (f'{is_panel} and ($1.shows or "") = ""', 'in:$2,prop:lens=$1.lens,-prop:shows'),
        (f'{is_panel} and ($1.shows or "") != ""', 'in:$2,prop:lens=$1.lens,prop:shows=$1.shows'),
        (is_lens, 'in:$2,prop:lens=$1.title,-prop:shows'),
    ]:
        removed = selection + ',prop:dock_removed=yes'
        pin.append(f'do prop {removed} dock_removed=no when {guard} and count({removed}) > 0')
    # Every lookup is inside the current layout, including nested columns.
    base = 'in:$2,prop:role=home-panel,prop:lens=$(($1.lens or 0))'
    valid_tree = '(($2.tree or "") = "" or tree-activate($2.tree, 0) != "")'
    opened = [
        '# dock-open <pin> <current layout> <current home-view>.',
        '# Current columns and the staged partition layout are both supported.',
        'table in:$2,prop:role=home-panel cols=lens,shows,shelf',
        'do create $2 kind=surface title=column layout=column when ($1.lens or "") != "" and ($2.tree or "") = "" and count(kind:surface,in:$2) = 0',
    ]
    for condition, selection in [
        ('($1.shows or "") = ""', base + ',-prop:shows'),
        ('($1.shows or "") != ""', base + ',prop:shows=$(($1.shows or 0))'),
    ]:
        guard = f'($1.lens or "") != "" and {condition} and {valid_tree}'
        opened += [
            f'do prop {selection},prop:shelf=yes shelf=no when {guard} and count({selection},prop:shelf=yes) > 0',
        ]
        for where, layout_guard in [
            ('$2', '($2.tree or "") != ""'),
            ('$(max($item of kind:surface,in:$2))', '($2.tree or "") = ""'),
        ]:
            opened.append(f'do create {where} kind=note title="$1.title" role=home-panel actor=$me lens=$1.lens shows={optional("shows")} shelf=no {shared} {policy} when {guard} and {layout_guard} and count({selection}) = 0')
        activation = f'tree-activate($2.tree, (max($item of {selection}) or 0))'
        opened.append(f'do prop $2 tree={value(activation)} when {guard} and ($2.tree or "") != "" and {activation} != $2.tree')
    opened += [
        f'do prop $2 full="" when ($1.lens or "") != "" and ($2.full or "") != "" and {valid_tree}',
        'do view $1.opens when ($1.opens or "") != "" and $1.opens != "chat"',
        'do unview $3 when ($1.opens or "") = "chat"',
    ]
    return {"dock-pin.verb": pin, "dock-open.verb": opened}


if __name__ == "__main__":
    for name, lines in build().items():
        (HERE / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
