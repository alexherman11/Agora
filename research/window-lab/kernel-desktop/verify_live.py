"""Read-only, bounded live desktop verification. No clicks, focus, or world writes."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import winreg

from kd_say import say
from taskbar_guard import LEASE, owner_alive, taskbars, u
from kd_window import monitor

HERE = Path(__file__).resolve().parent


def main():
    sessions = json.loads((HERE/'state/world/keep/sessions.json').read_text())
    token = next(t for t,v in sessions.items() if v.get('signer') == 'claude')
    def scene(name):
        request = urllib.request.Request('http://127.0.0.1:8810/api/scene?lens='+name,
                                         headers={'Authorization':'Bearer '+token})
        return json.loads(urllib.request.urlopen(request, timeout=20).read())
    lease = json.loads(LEASE.read_text())
    assert lease['ready'] and not lease['restored'] and owner_alive(lease)
    assert taskbars() and not any(u.IsWindowVisible(h) for h in taskbars())
    windows = say('window.list',token)['rows']
    bars = {w['edge']:w for w in windows if w.get('edge')}
    full, work = monitor()
    assert bars['top']['shown'] and bars['bottom']['shown']
    assert bars['top']['box'][1] == 0
    assert bars['bottom']['box'][1] + bars['bottom']['box'][3] == full[3]
    assert work[1] == bars['top']['box'][3] and work[3] == bars['bottom']['box'][1]
    tasks = [r for r in say('window.desktop',token)['rows'] if r.get('handle')]
    assert tasks and all(t.get('icon') for t in tasks if t.get('path'))
    assert '[icon] picture' in scene('topbar').get('text','')
    assert not scene('feed').get('refused')
    system = json.loads((HERE/'state/world/modules/system/live.json').read_text())
    assert time.time()-system['at'] < 15
    assert system.get('focused',{}).get('symbol')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        assert 'taskbar_guard.py' in winreg.QueryValueEx(key,'Agora taskbar recovery')[0]
    # WMI recovery must live outside the kernel's process tree, including launchers.
    output = subprocess.run(['powershell','-NoProfile','-Command',
        'Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress'],
        capture_output=True,text=True,timeout=20,creationflags=0x08000000).stdout
    parents = {r['ProcessId']:r['ParentProcessId'] for r in json.loads(output)}
    kernel = int((HERE/'state/world/keep/kdesk.pid').read_text())
    ancestors, p = set(), lease['guard']
    while p and p not in ancestors:
        ancestors.add(p)
        p = parents.get(p,0)
    assert kernel not in ancestors
    print('LIVE OK: kernel answering; '+str(len([w for w in windows if w.get('kind')=='window']))+' Agora windows; '+str(len(tasks))+' Windows task buttons; '+str(sum(bool(t.get('icon')) for t in tasks))+' executable icons; '+str(sum(not t.get('shown') for t in tasks))+' minimized windows included.')
    print(f'LIVE OK: top/bottom AppBars; work area {work}; Windows taskbar hidden; independent recovery guard; sign-in recovery registered; fresh system readings; Feed/topbar scenes compiled.')


if __name__ == '__main__':
    main()
