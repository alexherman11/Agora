"""Read-only five-minute gaming gate poll, at most ninety minutes."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'desktop/kernel-desktop'))
from gaming_gate import reasons


def main():
    history=[]
    for attempt in range(19):
        result=subprocess.run(['powershell.exe','-NoProfile','-Command',
            'Get-Process RocketLeague,*game* -ErrorAction SilentlyContinue | Select-Object ProcessName,Id | ConvertTo-Json -Compress'],
            capture_output=True,text=True,creationflags=0x08000000)
        try:processes=json.loads(result.stdout) if result.stdout.strip() else []
        except ValueError:processes=[]
        found=reasons()
        row=dict(at=datetime.now(timezone.utc).isoformat(),attempt=attempt,reasons=found,processes=processes)
        history.append(row)
        (HERE/'evidence/gaming-gate.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
        print('GATE',attempt,'clear' if not found else ', '.join(found),flush=True)
        if not found:return 0
        if attempt==18:return 2
        for _ in range(5):time.sleep(60)


if __name__=='__main__':raise SystemExit(main())
