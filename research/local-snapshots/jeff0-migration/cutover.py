"""One authorized idle handoff; original native data stays intact."""
import json
from pathlib import Path
import shutil
import sys

old = Path(r'C:\Projects\Agora\worlds\improved-desk')
new = Path(r'C:\Projects\Agora\worlds\jeff0-desk')
repo = Path(r'C:\Projects\Agora\worlds\application-experiment\repo')
sys.path[:0] = [str(old), str(repo/'scripts'), str(repo/'src')]
import control_client as c
from migrate_resident import migrate

if (new/'world').exists():
    raise RuntimeError('Destination world already exists; nothing replaced.')
status = c.call({'op':'status'})
if status['running'] or status['error']:
    raise RuntimeError('Original JEFF is busy or needs attention; no handoff performed.')
observer=c.browser(op='evaluate',expression="({draft:document.querySelector('#chat-input')?.value, inputs:[...document.querySelectorAll('textarea')].map(n=>({id:n.id,value:n.value,start:n.selectionStart,end:n.selectionEnd}))})")
(Path(__file__).parent/'cutover-observer-state.json').write_text(json.dumps(observer,indent=2),encoding='utf8')
print(c.call({'op':'close'}),flush=True)
report=migrate(old/'world',new/'world',observer=observer)
for name in ('open_desk.py','serve_desk.py'):
    shutil.copy2(old/name,Path(__file__).parent/('original-'+name))
launcher=(old/'open_desk.py').read_text(encoding='utf8')
launcher=launcher.replace('def main():\n', 'def main():\n    moved = ROOT / "moved.json"\n    if moved.exists():\n        target = Path(json.loads(moved.read_text())["destination"])\n        return subprocess.run([sys.executable, str(target / "open_desk.py"), *sys.argv[1:]], cwd=target, check=True)\n')
(old/'open_desk.py').write_text(launcher,encoding='utf8')
service=(old/'serve_desk.py').read_text(encoding='utf8')
service=service.replace('def main():\n', 'def main():\n    if (ROOT / "moved.json").exists():\n        raise SystemExit("JEFF0 moved. Use Open Agora Desk to open his continuing world.")\n')
(old/'serve_desk.py').write_text(service,encoding='utf8')
(old/'moved.json').write_text(json.dumps({'resident':'jeff0','destination':str(new),'original_native_journal_retained':True},indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in {'drafts','views'}},indent=2),flush=True)
