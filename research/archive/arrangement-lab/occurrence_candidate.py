"""Bounded implementation of the supplied transcript's independent board occurrences.
Transforms pinned package source only; publishing still uses native package operations.
"""

from copy import deepcopy


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Pinned source no longer matches the reviewed change: " + old[:80])
    return source.replace(old, new, 1)


def board_candidate(source):
    source = deepcopy(source)
    code = source["files"]["boards.py"]
    code = replace_once(
        code,
        "    if find(ctx,id):raise ValueError('Note identity already exists. "
        "Refresh before retrying.')",
        "    if find(ctx,id):raise ValueError('Note identity already exists. "
        "Refresh before retrying.')\n"
        "    if any(p['id']==id for p in b['items']):"
        "raise ValueError('Occurrence identity already exists on this board.')",
    )
    code = replace_once(
        code,
        "    if any(p['note_id']==n['id'] for p in b['items']):raise ValueError('This note is already on the board.')",  # noqa: E501 - exact source match or retained trial prompt
        "    occurrence=args.get('occurrence_id',n['id'])\n"
        "    if 'occurrence_id' not in args and any(p['note_id']==n['id'] for p in b['items']):raise ValueError('This note is already on the board. Supply a new occurrence_id to add another appearance.')\n"  # noqa: E501 - exact source match or retained trial prompt
        "    if any(p['id']==occurrence for p in b['items']):raise ValueError('Occurrence identity already exists on this board.')",  # noqa: E501 - exact source match or retained trial prompt
    )
    code = replace_once(
        code,
        "b['items'].append({'id':n['id'],'note_id':n['id']",
        "b['items'].append({'id':occurrence,'note_id':n['id']",
    )
    code = replace_once(
        code,
        "return ok({'note_id':n['id']},[change(o,{'notes.board':b})])",
        "return ok({'note_id':n['id'],'occurrence_id':occurrence},[change(o,{'notes.board':b})])",
    )
    code = replace_once(
        code,
        "    b['items']=[p for p in b['items'] if p['note_id']!=args['note_id']]",
        "    matches=[p for p in b['items'] if p['note_id']==args['note_id'] and ('occurrence_id' not in args or p['id']==args['occurrence_id'])]\n"  # noqa: E501 - exact source match or retained trial prompt
        "    if len(matches)!=1:raise ValueError('Identify exactly one appearance with occurrence_id; no appearances removed.')\n"  # noqa: E501 - exact source match or retained trial prompt
        "    b['items']=[p for p in b['items'] if p['id']!=matches[0]['id']]",
    )
    source["files"]["boards.py"] = code
    for name in ("add_note", "remove_note"):
        action = source["manifest"]["actions"][name]
        action["input_schema"]["properties"]["occurrence_id"] = {
            "type": "string",
            "minLength": 1,
            "maxLength": 160,
        }
    source["manifest"]["actions"]["add_note"]["description"] += (
        " Optional occurrence_id adds an independent appearance of an already-present note. "
        "Use a unique occurrence ID; content is still shared. Omit for legacy deduplication."
    )
    source["manifest"]["actions"]["remove_note"]["description"] += (
        " Supply occurrence_id when a subject appears more than once; ambiguous removal refuses."
    )
    source["files"]["usage.md"] += (
        "\n\nOccurrence identity: item.id addresses placement; item.note_id "
        "addresses shared content. add_note accepts an optional unique occurrence_id. "
        "remove_note requires occurrence_id when several appearances share note_id. "
        "layout continues to accept occurrence IDs in patches[].id.\n"
    )
    return source


def notes_candidate(source):
    source = deepcopy(source)
    code = source["files"]["board.js"]
    for old, new in [
        ("wanted.add(p.note_id);", "wanted.add(p.id);"),
        ("this.cards.get(p.note_id);", "this.cards.get(p.id);"),
        ("this.cards.set(p.note_id,c);", "this.cards.set(p.id,c);"),
        ("c.el.dataset.note=obj.id;", "c.el.dataset.note=obj.id;c.el.dataset.occurrence=p.id;"),
        ("const draft=this.drafts[obj.id];", "const draft=this.drafts[p.id];"),
        (
            "this.operation('remove_note',{note_id:obj.id,board_revision:this.board.revision})",
            "this.operation('remove_note',{note_id:obj.id,occurrence_id:p.id,board_revision:this.board.revision})",  # noqa: E501 - exact source match or retained trial prompt
        ),
        (
            "this.mutate('add_note',{note_id:obj.id,x:old.x,y:old.y,color:old.color})",
            "this.mutate('add_note',{note_id:obj.id,occurrence_id:old.id,x:old.x,y:old.y,color:old.color})",  # noqa: E501 - exact source match or retained trial prompt
        ),
        (".items.find(p=>p.note_id===c.object.id);", ".items.find(p=>p.id===c.placement.id);"),
        (
            "for(const o of items)if(!this.board.facets['notes.board'].items.some(p=>p.note_id===o.id))select.append(new Option(o.title||'Untitled',o.id));",  # noqa: E501 - exact source match or retained trial prompt
            "for(const o of items){const present=this.board.facets['notes.board'].items.some(p=>p.note_id===o.id);select.append(new Option((o.title||'Untitled')+(present?' — another appearance':''),o.id));}",  # noqa: E501 - exact source match or retained trial prompt
        ),
        (
            "const note_id=select.value;const placement=this.placement();dialog.close();dialog.remove();await this.mutate('add_note',{note_id,...placement,color:'blue'});this.cards.get(note_id)?.input.focus({preventScroll:true});",  # noqa: E501 - exact source match or retained trial prompt
            "const note_id=select.value;const present=this.board.facets['notes.board'].items.some(p=>p.note_id===note_id);const occurrence_id=present?'occurrence-'+crypto.randomUUID():note_id;const placement=this.placement();dialog.close();dialog.remove();await this.mutate('add_note',{note_id,occurrence_id,...placement,color:'blue'});this.cards.get(occurrence_id)?.input.focus({preventScroll:true});",  # noqa: E501 - exact source match or retained trial prompt
        ),
    ]:
        code = replace_once(code, old, new)
    source["files"]["board.js"] = code
    return source
