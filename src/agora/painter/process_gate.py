"""EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
needs something, the general form of it is the change.

Screen gate: games AND any full-screen foreground application block adoption."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'desktop/kernel-desktop'))
from gaming_gate import reasons


def check():
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',
        'Get-Process RocketLeague,*game* -ErrorAction SilentlyContinue | Select-Object ProcessName,Id | ConvertTo-Json -Compress'],
        capture_output=True,text=True,creationflags=0x08000000)
    # The existing process scanner knows helper services and more game names.
    blocked=reasons()
    record=dict(at=datetime.now(timezone.utc).isoformat(),blocked=blocked,
                process_check=json.loads(result.stdout) if result.stdout.strip() else [])
    if blocked:raise RuntimeError('Gaming gate: '+', '.join(blocked))
    return record


if __name__=='__main__':print(json.dumps(check()),flush=True)
