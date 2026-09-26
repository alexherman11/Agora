"""Mutual exclusion of explore.take_lock across processes, with crashing holders.

python mutex.py <notation dir> <workers> <iterations> <crash_every>
Each worker: take the lock, enter a critical section guarded by an O_EXCL marker (a second holder inside is a
violation), bump a counter file, leave, release. Every crash_every-th acquisition the worker dies holding the lock.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

WORKER = r'''
import os, sys, time, random
sys.path.insert(0, sys.argv[1])
import explore
lock, marker, counter, log = (os.path.join(sys.argv[2], n) for n in ("s.lock", "inside", "counter", "violations"))
its, crash_every, wid = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
from pathlib import Path
for i in range(its):
    lease = explore.take_lock(Path(lock), tries=100000, pause=0.001)
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
    except FileExistsError:
        with open(log, "a") as f: f.write(f"w{wid} i{i}\n")
    n = int(open(counter).read() or 0) if os.path.exists(counter) else 0
    time.sleep(random.random() * 0.002)
    open(counter, "w").write(str(n + 1))
    if crash_every and (wid * 1000 + i) % crash_every == 0:
        try: os.unlink(marker)
        except OSError: pass
        os._exit(3)                        # die holding the lock
    try: os.unlink(marker)
    except OSError: pass
    if hasattr(explore, "release_lock"):
        explore.release_lock(lease)
    else:
        Path(lock).unlink(missing_ok=True)   # main's protocol: release by unlinking
'''

def main():
    notation, workers, its, crash = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    tmp = Path(sys.argv[5]); tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.iterdir(): f.unlink()
    (tmp / "w.py").write_text(WORKER)
    t0 = time.time()
    ps = [subprocess.Popen([sys.executable, str(tmp / "w.py"), notation, str(tmp), str(its), str(crash), str(k)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) for k in range(workers)]
    errs = []
    for p in ps:
        out, err = p.communicate(timeout=600)
        if p.returncode not in (0, 3):
            errs.append(err.decode()[-300:])
    counter = int((tmp / "counter").read_text()) if (tmp / "counter").exists() else 0
    viol = (tmp / "violations").read_text().splitlines() if (tmp / "violations").exists() else []
    print(f"{Path(notation).parts[-4]}: workers={workers} its={its} crash_every={crash} time={time.time()-t0:.1f}s "
          f"counter={counter} violations={len(viol)} worker_errors={len(errs)}")
    for e in errs[:2]:
        print("  err:", e.strip().splitlines()[-1] if e.strip() else e)

main()
