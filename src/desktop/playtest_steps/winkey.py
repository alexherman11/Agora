from playtest_steps import Step
from playtest_steps._support import HERE, PY, asyncio, subprocess


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_winkey():
        play.needs("a5980", "the Windows key")
        p = await asyncio.to_thread(subprocess.run, [PY, str(HERE / "test_winkey.py")], capture_output=True, text=True, timeout=180)
        lines = (p.stdout or "").strip().splitlines()
        fails = [x for x in lines if x.startswith("FAIL")]
        if p.returncode or fails:
            raise AssertionError(f"test_winkey.py: {len(fails)} failed: " + "; ".join(fails[:3]) + (f" (exit {p.returncode})" if p.returncode else ""))
        return {"note": f"no key is sent: test_winkey.py drives the tap logic and the hook with made-up keys ({sum(x.startswith('ok') for x in lines)} ok)"}
    return s_winkey


STEP = Step(name='winkey', description='the Windows key shows and hides it (test_winkey.py)', order=2700,
            needs=(('a5980', 'the Windows key'),), script=bind, assertion='the Windows key shows and hides it (test_winkey.py)', budget=(100, 300))
