"""A hidden copy of Alex's desktop world, run inside this process (so a headless browser here is a guarded widget host).

Same set-up as desktop/kernel-desktop/sandbox.py `run`: modules headless, outside-reaching ones off, the house off
(no live model), no window on the screen. The live world (state/world) is only read, once, when copying.
    with Sandbox('claude-writing') as s: s.url, s.door(who)
"""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DESKTOP = ROOT / 'src/desktop/kernel-desktop'
sys.path[:0] = [str(ROOT / 'src/agora'), str(DESKTOP)]
import sandbox  # noqa: E402


class Sandbox:
    def __init__(self, name='claude-writing'):
        self.name = name

    def __enter__(self):
        import kdesk
        from kernel.kernel import Tx
        sandbox.fresh(self.name)
        world = sandbox.world_dir(self.name)
        os.environ.pop('HOUSE_FAKE_MODEL', None)
        self.k, self.srv, self.host, self.entry = kdesk.start(world, 0, modules=False, headless=True)
        k = self.k
        with k.lock:
            tx = Tx(k)
            tx.part('install', None, 'install')
            for m in k.things('module'):
                nm, argv = k.state.get(m, 'name'), list(k.state.get(m, 'run') or [])
                if (nm in sandbox.OFF or nm == 'house') and k.state.get(m, 'on'):
                    tx.set(m, 'on', False)
                elif nm in sandbox.HEADLESS and '--headless' not in argv:
                    tx.set(m, 'run', argv + ['--headless'])
                elif nm not in sandbox.HEADLESS | sandbox.OFF | {'theme', 'board', 'files', 'house'} and k.state.get(m, 'on'):
                    tx.set(m, 'on', False)
            k._commit(tx, by='kernel', words='sandbox: modules headless, outside-reaching modules off')
        self.host.reconcile()
        self.url = f'http://127.0.0.1:{self.srv.server_address[1]}'
        self.stop = threading.Event()
        threading.Thread(target=self._keep, daemon=True).start()
        return self

    def _keep(self):
        while not self.stop.wait(2):
            try:
                self.host.reconcile()
            except Exception:
                pass

    def __exit__(self, *exc):
        self.stop.set()
        try:
            self.host.stop_all()
        finally:
            self.srv.shutdown()
            self.srv.server_close()
            # the copy holds the world's session keys: do not leave it lying about
            import shutil
            shutil.rmtree(sandbox.world_dir(self.name), ignore_errors=True)
