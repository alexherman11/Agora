import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path('C:/Projects/Agora3')
SOURCE = ROOT / 'src/agora3'
shutil.copytree(REPO / 'src/agora3', SOURCE, dirs_exist_ok=True)
shutil.copytree(REPO / 'tests', ROOT / 'tests', dirs_exist_ok=True)
shutil.copy(REPO / 'pyproject.toml', ROOT / 'pyproject.toml')
shutil.copy(ROOT / 'chat_activity.py', SOURCE / 'chat_activity.py')

server = (SOURCE / 'server.py').read_text()
server = server.replace('from agora3.bridge import NativeBridge', 'from agora3.bridge import NativeBridge\nfrom agora3.chat_activity import ChatActivity')
server = server.replace('self.jeff = self.jeff_identity = None', 'self.activity = ChatActivity()\n        self.jeff = self.jeff_identity = None')
server = server.replace('"events": self.events[-30:],', '"events": self.events[-30:],\n                "activity": self.activity.snapshot(),')
server = server.replace('self.running, self.reply, self.error, self.events = True, "", None, []', 'self.running, self.reply, self.error, self.events = True, "", None, []\n            self.activity = ChatActivity()')
server = server.replace('self.events.append(event)', 'self.activity.observe(event)\n                self.events.append(event)')
(SOURCE / 'server.py').write_text(server, encoding='utf-8')

jeff = (SOURCE / 'jeff.py').read_text()
jeff = jeff.replace('self._emit({"type": "text.delta", "text": event.payload.delta})', '''message_event = {"type": "text.delta", "text": event.payload.delta}
                    item_id = getattr(event.payload, "item_id", None)
                    if item_id:
                        message_event["id"] = item_id
                    self._emit(message_event)''')
jeff = jeff.replace('elif event.method == "item/completed":', 'elif event.method in {"item/started", "item/completed"}:')
jeff = jeff.replace('if getattr(item, "type", None) == "agentMessage" and phase == "final_answer":\n                        final_messages.append(item.text)', '''if getattr(item, "type", None) == "agentMessage":
                        completed = event.method == "item/completed"
                        self._emit({
                            "type": "text.completed" if completed else "text.started",
                            "id": getattr(item, "id", None) or "legacy",
                            "text": getattr(item, "text", ""),
                            "phase": phase or "commentary",
                        })
                        if completed and phase == "final_answer":
                            final_messages.append(item.text)''')
(SOURCE / 'jeff.py').write_text(jeff, encoding='utf-8')
prompt_path = SOURCE / 'prompts/jeff.md'
prompt = prompt_path.read_text(encoding='utf-8')
prompt += '\nDuring multi-step work, send a brief user-facing progress message before\nsubstantial tool work and at meaningful milestones, especially when tests reveal\na problem or the approach changes. Describe the current action or finding in\nplain language; avoid narrating every tool call. These messages appear live in\nthe conversation. Do not defer all communication until the final answer.\n'
prompt_path.write_text(prompt, encoding='utf-8')

def patch_html(html):
    start = html.index('  function renderChat(status) {')
    end = html.index('  async function sendMessage(', start)
    html = html[:start] + (ROOT / 'chat-render.js').read_text() + '\n' + html[end:]
    html = html.replace('  </style>', (ROOT / 'chat.css').read_text() + '\n  </style>')
    vendors = '\n'.join((ROOT / f'{name}.js').read_text(encoding='utf-8').replace('</script', '<\\/script') for name in ['marked', 'dompurify'])
    html = html.replace('  <script>', '  <script>\n' + vendors + '\n</script>\n  <script>', 1)
    html = html.replace('setInterval(refreshChat,2000)', 'setInterval(refreshChat,500)')
    return html

baseline = SOURCE / 'builtin/shell/index.html'
baseline.write_text(patch_html(baseline.read_text(encoding='utf-8')), encoding='utf-8')
package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8-sig'))
files = package['facets']['agora.package']['files']
files['index.html'] = patch_html(files['index.html'])
files['CHAT.md'] = '''# Chat presentation

Assistant messages render GitHub-flavored Markdown using vendored Marked 18.0.12
and DOMPurify 3.4.15. HTML is sanitized against a small presentation allowlist;
remote images, executable elements, styles and unsafe links are excluded.
User text remains literal. Code blocks and tables scroll within the chat panel.

chat.status.activity supplies per-message snapshots keyed by turn and item ID.
Commentary and the streaming final answer remain separate. The durable final
replaces its streamed counterpart. Activity includes a tool label and elapsed
time, never raw commands. Progress survives view reload and missed polls within
the current server session; it is transient and resets on the next request or
server restart. No raw reasoning is displayed. Existing note behavior is retained.
'''
licenses = []
for name in ['marked','dompurify']:
    content = (ROOT / f'{name}.js').read_bytes()
    licenses.append(f'## {name}\nSHA-256: {hashlib.sha256(content).hexdigest()}\n\n' + (ROOT / f'{name}-LICENSE').read_text())
license_text = '# Vendored chat dependencies\n\n' + '\n\n'.join(licenses)
files['CHAT-DEPENDENCIES.md'] = license_text
(SOURCE / 'builtin/shell/CHAT-DEPENDENCIES.md').write_text(license_text,encoding='utf-8')
(ROOT / 'candidate.html').write_text(files['index.html'],encoding='utf-8')
(ROOT / 'candidate.json').write_text(json.dumps(package,ensure_ascii=False),encoding='utf-8')
print('Prepared source, baseline shell and native candidate from source',package['revision'])
