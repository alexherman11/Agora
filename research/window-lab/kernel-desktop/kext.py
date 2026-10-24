"""kext: what the desktop still adds to the kernel, as a small extension in this folder.

Claude (PROOF a13428), 23 Oct 2026. Until 19:36 this file added rows, verb notes, rules, a module acting on its own,
narrowed grants and a fuller hello. The kernel builder took all of them into the kernel (commit 2d872eb), so they are
gone from here. What is left:

    a log file per module      what a module says on stderr also goes to <world>/logs/<module>.log, so a module that
                               fails at 3 am can be read the next morning (the kernel keeps its last 20 lines only).

It imports research/kernel-lab/kernel unchanged; nothing in kernel-lab is edited.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "kernel-lab"
sys.path.insert(0, str(LAB))

from kernel import modules as KM                                # noqa: E402
from kernel.kernel import Kernel                                # noqa: E402


class DeskModuleProcess(KM.ModuleProcess):
    """The kernel's module process, plus a log file of what the module says on stderr."""

    def _read_err(self):
        k = self.host.kernel
        try:
            logs = Path(k.dir) / "logs"
            logs.mkdir(exist_ok=True)
            fh = open(logs / f"{k.state.get(self.mid, 'name') or self.mid}.log", "a", encoding="utf-8")
            fh.write(f"--- started {time.strftime('%Y-%m-%d %H:%M:%S')} pid {self.proc.pid}\n")
            fh.flush()
        except OSError:
            fh = None                                   # no log file (a test world already gone): keep the last lines only
        for line in self.proc.stderr:
            self.err = (self.err + [line.rstrip()])[-20:]
            if fh:
                try:
                    fh.write(line)
                    fh.flush()
                except (OSError, ValueError):
                    fh = None
        if fh:
            fh.close()


# the kernel's Host makes its processes by this module-level name (kernel/modules.py); in this process they are ours
KM.ModuleProcess = DeskModuleProcess
DeskKernel = Kernel
DeskHost = KM.Host
