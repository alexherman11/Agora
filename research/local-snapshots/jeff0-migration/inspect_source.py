import json
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Projects\Agora\worlds\improved-desk')
import control_client as c

root = Path(__file__).parent
print(json.dumps(c.call({'op': 'status'}), default=str))
value = c.browser(op='evaluate', expression="""({
    draft: document.querySelector('#chat-input')?.value,
    inputs: [...document.querySelectorAll('textarea')].map(n=>({id:n.id,value:n.value,start:n.selectionStart,end:n.selectionEnd}))
})""")
(root / 'final-observer-state.json').write_text(json.dumps(value, indent=2), encoding='utf8')
print({'observer_draft_length': len(value.get('draft') or '')})
result = c.rpc('guest.execute', {'command': "sudo find /root/agora-editor-build -maxdepth 2 -type f -printf '%P %s bytes\\n' | head -40", 'timeout': 20})
(root / 'guest-build-inventory.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(result)
