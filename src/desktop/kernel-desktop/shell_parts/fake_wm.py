"""fake_wm: a stand-in window manager for hidden tests of the shell components (test_shell_components.py).

Offers the words the bars speak (wm.windows, wm.focus, wm.minimise, wm.restore, wm.close, wm.pin, wm.unpin) over a
fixed set of pretend windows kept in memory, with keys shaped like the real manager's (pid:created:hwnd). It touches no
real window. wm.calls (see) lists what it was asked, for the test to read back. Run by a scratch kernel only:
    module wm run=["<python>", "<this file>"] grants="rows look"
"""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modproto import Module  # noqa: E402

SYS = 'C:\\Windows\\System32\\'
APPS = [('Notepad', SYS + 'notepad.exe', 2), ('Paint', SYS + 'mspaint.exe', 1), ('Task Manager', SYS + 'Taskmgr.exe', 1)]


class FakeWM:
    def __init__(self):
        self.lock = threading.Lock()
        self.calls = []
        self.rows = []
        hwnd = 5001
        for i, (app, exe, n) in enumerate(APPS):
            for j in range(n):
                self.rows.append({'key': f'{4000 + i}:77:{hwnd}', 'app': app, 'exe': exe, 'icon': exe, 'agora': '',
                                  'state': 'normal', 'focused': i == 0 and j == 0, 'rect': [0, 0, 800, 600], 'space': '',
                                  'managed': True, 'why': ''})
                hwnd += 1
        words = {'windows': 'see', 'calls': 'see', 'focus': 'do', 'minimise': 'do', 'restore': 'do', 'close': 'do', 'pin': 'do', 'unpin': 'do'}
        self.m = Module([{'word': 'wm.' + w, 'kind': k, 'takes': '' if k == 'see' else '<key>', 'may': 'anyone',
                          'help': f'wm.{w}: a stand-in window manager for hidden tests'} for w, k in words.items()], self.call)

    def call(self, msg):
        word = msg['word'].removeprefix('wm.')
        args = msg.get('args') or {}
        kv, words = args.get('kv') or {}, str(args.get('words') or '').split()
        key = kv.get('key') or args.get('target') or (words[0] if words else '')
        with self.lock:
            if word == 'windows':
                return {'rows': [dict(r) for r in self.rows], 'text': f'{len(self.rows)} windows; live'}
            if word == 'calls':
                return {'rows': [{'line': c} for c in self.calls], 'text': '\n'.join(self.calls)}
            self.calls.append(f'wm.{word} {key}')
            row = next((r for r in self.rows if r['key'] == key), None)
            if row is None:
                return {'refused': 'choose a current window from wm.windows'}
            if word in ('focus', 'restore'):
                for r in self.rows:
                    r['focused'] = False
                row.update(focused=True, state='normal')
            elif word == 'minimise':
                row.update(focused=False, state='minimised')
            elif word == 'close':
                self.rows.remove(row)
            elif word in ('pin', 'unpin'):
                row['state'] = 'pinned' if word == 'pin' else 'normal'
            return {'external': True, 'text': f'wm.{word}: requested'}

    def run(self):
        self.m.run_reader()
        self.m.closed.wait()


if __name__ == '__main__':
    FakeWM().run()
