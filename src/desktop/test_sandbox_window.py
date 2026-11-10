"""test_sandbox_window: the guard of sandbox_window.py must FAIL when Alex is touched, and only then (a5932).

    python src/desktop/test_sandbox_window.py          the guard's judgement, on scripted samples (no window)
    python src/desktop/test_sandbox_window.py --live   also the real self-test: sandbox_window.py test webview

The scripted half feeds the Guard what it would read (his foreground, focus, cursor, input desktop, the time of the last
real input, the sandbox's windows, his windows) and checks its verdict, so the failing side is proven without touching
his screen to prove it.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sandbox_window as sw  # noqa: E402

BASE = {"foreground": 100, "focus": 101, "cursor": (500, 500), "input desktop": "Default"}


def judge(samples, ours=(), his_titles=(), inputs=None, far=True, crash=False):
    """Run a Guard over a script of states (and last-input times), -> its (code, words)."""
    states, times = iter(samples), iter(inputs or [1000] * len(samples))
    last = {"s": BASE, "t": 1000}

    def next_state():
        last["s"] = next(states, last["s"])
        return last["s"]

    def next_input():
        last["t"] = next(times, last["t"])
        return last["t"]
    real = (sw._alex, sw.last_input, sw.ticks, sw.owner, sw.exe)
    sw._alex, sw.last_input = next_state, next_input
    sw.owner, sw.exe = lambda hwnd: 0, lambda pid: "fixture"
    sw.ticks = lambda: last["t"] + (10_000 if far else 20)       # his last input long ago (far), or just now
    try:
        g = sw.Guard("scripted", "sandbox test")
        g.sandbox_windows = lambda: set(ours)
        g.his_windows = (lambda: 1 / 0) if crash else (lambda: [(1, 0, 0, 10, 10, t) for t in his_titles])
        with g:
            time.sleep(0.4)
        return g.verdict()
    finally:
        sw._alex, sw.last_input, sw.ticks, sw.owner, sw.exe = real


def main():
    moved = dict(BASE, cursor=(501, 500))
    cases = [
        ("nothing changes", [BASE], {}, 0),
        ("the cursor moves with no input from anyone", [BASE, moved], {}, 1),
        ("the cursor moves as he moves the mouse", [BASE, moved], {"inputs": [1000, 1016]}, 0),
        ("a 1-pixel move inside one input tick, just after his input", [BASE, moved], {"far": False}, 0),
        ("a sandbox window becomes his foreground", [BASE, dict(BASE, foreground=777, focus=777)], {"ours": [777]}, 1),
        ("the same, while he is typing", [BASE, dict(BASE, foreground=777)], {"ours": [777], "inputs": [1000, 1016]}, 1),
        ("the input desktop changes", [BASE, dict(BASE, **{"input desktop": "agora-sandbox-x"})], {}, 1),
        ("a window titled like ours shows on his desktop", [BASE], {"his_titles": ["sandbox test - Edge"]}, 1),
        ("his own app takes the foreground by itself", [BASE, dict(BASE, foreground=555, focus=555)], {}, 0),
        ("the guard itself breaks (it must not then say untouched)", [BASE], {"crash": True}, 1),
    ]
    bad = 0
    for what, samples, kw, want in cases:
        code, words = judge(samples, **kw)
        ok = code == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {what}: {'fails' if code else 'passes'} ({words[:110]})")
    if "--live" in sys.argv:
        r = subprocess.run([sys.executable, str(HERE / "sandbox_window.py"), "test", "webview"])
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} the live self-test (exit {r.returncode})")
        bad += r.returncode != 0
    print("all passed" if not bad else f"{bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
