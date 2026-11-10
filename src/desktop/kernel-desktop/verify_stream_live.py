"""Bounded live acceptance check. Opens eight native windows by words, then
closes only those windows in finally. A headless browser checks the Lines form.
Run after kdesk_off.py / detached kdesk_on.py --wait, with pinned Python.
"""
import json
import os
from pathlib import Path
import subprocess
import time

from hidden_evidence import Browser
from kd_say import say
from test_stream_windows import window_url, lines_help

HERE = Path(__file__).resolve().parent


def main():
    sessions = json.loads((HERE / 'state/world/keep/sessions.json').read_text())
    token = next(t for t, v in sessions.items() if v.get('signer') == 'alex')
    def words(line):
        out = say(line, token)
        assert out.get('ok', True), out
        return out
    def windows():
        return [w for w in words('window.list')['rows'] if w.get('kind') == 'window']
    def wait(predicate, seconds=30):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            result = predicate()
            if result:
                return result
            time.sleep(.2)
        raise AssertionError('live windows did not become shown')
    baseline = windows()
    keep = {w['id'] for w in baseline}
    created = set()
    try:
        for view in ('feed', 'help', 'lines', 'feed', 'help', 'lines', 'feed', 'help'):
            count = len(windows())
            words('window.open ' + view + ' new=yes')
            wait(lambda: len(ws := windows()) == count + 1 and all(w['shown'] for w in ws))
        current = wait(lambda: (ws if len(ws := windows()) == len(baseline) + 8
                               and all(w['shown'] for w in ws) else None))
        created = {w['id'] for w in current} - keep
        assert len(created) == 8
        # netstat is taken before headless Edge: client rows belong to the live
        # desktop, not the hidden verification browser.
        kernel = int((HERE / 'state/world/keep/kdesk.pid').read_text())
        browser_ids = set(map(int, subprocess.check_output(['powershell', '-NoProfile', '-Command',
            'Get-Process msedgewebview2 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],
            text=True, creationflags=0x08000000).split()))
        def connections():
            raw = subprocess.check_output(['netstat', '-ano', '-p', 'tcp'], text=True, creationflags=0x08000000)
            rows = [r.split() for r in raw.splitlines() if r.strip().startswith('TCP')]
            listeners = {r[1] for r in rows if r[3] == 'LISTENING' and int(r[4]) == kernel}
            cs = [r for r in rows if r[3] == 'ESTABLISHED' and r[2] in listeners and int(r[4]) in browser_ids]
            print(f'LIVE waiting: {len(listeners)} listeners; {len({r[2] for r in cs})} WebView origins connected', flush=True)
            return cs if len({r[2] for r in cs}) >= len(current) else None
        clients = wait(connections)
        ports = {r[2] for r in clients}
        assert len(ports) >= len(current), (len(current), clients)
        process_ids = sorted({int(r[4]) for r in clients})
        command = 'Get-Process -Id ' + ','.join(map(str, process_ids)) + ' | Select-Object Id,ProcessName | ConvertTo-Json -Compress'
        names = subprocess.check_output(['powershell', '-NoProfile', '-Command', command], text=True, creationflags=0x08000000).strip()
        print(f'LIVE netstat: {len(current)} shown Agora windows; {len(clients)} ESTABLISHED client connections across {len(ports)} kernel listener ports; processes={names}', flush=True)
        for r in clients:
            print('  ' + ' '.join(r), flush=True)
        lines = next(w for w in current if w['shows'] == 'lines' and w['id'] in keep)
        with Browser() as c:
            c.call('Page.navigate', url=window_url('http://127.0.0.1:8810', token, lines['id'],
                                                  '/desk/lines.html?win=' + lines['id']))
            c.until("location.pathname==='/desk/lines.html' && typeof KD !== 'undefined'")
            ms = lines_help(c)
            print(f'LIVE hidden Lines help: {ms:.1f} ms (<1000 ms) while eight extra native windows are open', flush=True)
    finally:
        # Include any successful opens even if a later open or assertion failed.
        created |= {w['id'] for w in windows()} - keep
        for wid in created:
            words('window.close ' + wid)
        wait(lambda: {w['id'] for w in windows()} == keep)
        restored = windows()
        board = next(w for w in restored if w['shows'] == 'taskboard')
        assert board['shown'], board
        print(f'LIVE restored: {len(restored)} original Agora windows; eight extras closed; Task board shown=True', flush=True)


if __name__ == '__main__':
    main()
