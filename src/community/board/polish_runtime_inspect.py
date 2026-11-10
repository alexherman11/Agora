"""Read-only capability check; never opens or alters a window."""
import json
from ui_live import taskboard, Gate

Gate()('inspect running compiler without altering windows')
door=taskboard.live_door()
lens=door.rows('lens',name='seabright-board')[0]
plan=door.request('/see',dict(line='look-view '+lens['id']+' plan=yes'))
row=plan.get('rows',[{}])[0]
print(json.dumps(dict(ok=plan.get('ok'),viewer=row.get('tree',{}).get('viewer'),
    tree_keys=list(row.get('tree',{})),errors=row.get('style_errors'),
    windows=[dict(title=w.get('title'),name=w.get('name'),want=w.get('want'),state=w.get('state')) for w in door.rows('window')]),sort_keys=True))
