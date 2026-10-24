"""paint: the one guarded paint lane (a10672, JEFF for Alex: agents look before they show him).

    python research/window-lab/paint/paint.py <lens> [--world frontier] [--as alex] [--sizes 1280x800,2560x1440]
                                              [--crop <part key>]... [--region x,y,w,h]...
                                              [--to <resident> --target <card> [--prompt "..."] --sign <actor>]

For each size, in order: the house's game-state admission (guard_context; refused: nothing starts); Alex's guard
(sandbox_window.Guard: his foreground, focus, cursor and input desktop, every 20 ms); a held Job (job_scope), so Edge and
every process it starts are one family; Edge on a hidden desktop of its own, opened on a COPY of the world (its log
caught up, served by its own door with this checkout's painter); the lens drawn and steady; then the shots, and the
Job's cleanup observed empty. Nothing reaches the real world or Alex's screen.

Shots, all from the browser's own renderer (Page.captureScreenshot), each with its sha256, pixel size and clip:
  01-full        the whole page as painted (evidence; at 2560 CSS px and Alex's 150 % it is 3840 px wide)
  02-overview    the whole page drawn smaller by the browser to fit 2048 px (only when 01 does not fit)
  NN-<name>      each --crop (a painted part, by its data-key) or --region (CSS px), split into tiles of at most
                 2048 px a side when larger, so a 2560 shot can still be delivered
A run is a folder demos/combined-review/<date-time>-<size>/ with report.json in the form guarded_artifacts reads
(Guard verdict, one row listing the deliverable shots); --to delivers each through guarded_artifacts --send, one
addressed image comment per shot on --target. A failed launch is recorded, never retried: the stage it reached, the
error, whether DevTools still answered, the cleanup receipt, and this process's token (restricted or not), since the
lane is known to differ by runtime (a10672: Codex workers run inside Codex's unelevated Windows sandbox).
"""
import argparse
import base64
import ctypes
import hashlib
import io
import json
import math
import os
import pickle
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
WL = HERE.parent
LAB = WL.parent / "text-desk-lab" / "notation"
sys.path[:0] = [str(WL), str(LAB)]

LIMIT = 2048                    # guarded_artifacts / image_comments: at most this many pixels a side
DEMO_ROOT = Path("C:/Projects/Agora4/research/window-lab/demos/combined-review")    # where guarded_artifacts reads
DELIVERABLE = ("1280x800", "2560x1440")       # the sizes guarded_artifacts admits as a run name
PY = sys.executable


# ---- pure parts (test_paint.py) ---------------------------------------------------------------------------------------

def slug(text, n=40):
    return (re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-") or "part")[:n]


def run_name(size, t=None):
    return time.strftime("%Y-%m-%d-%H%M%S", time.localtime(t)) + f"-{size}"


def fits(px):
    return all(1 <= v <= LIMIT for v in px)


def accepted(rep):
    """A painted row alone is not acceptance or permission to deliver an image."""
    return (rep.get("rows", [{}])[0].get("outcome") == "pass"
            and rep.get("guard", [1])[0] == 0
            and rep.get("cleanup", {}).get("ok") is True
            and rep.get("verification", {}).get("allow_interaction") is True
            and rep.get("post_admission", {}).get("admitted") is True
            and not rep.get("missing")
            and not rep.get("error"))


def overview_scale(iw, ih, dpr):
    """The clip scale at which the browser draws the whole page within LIMIT px a side (1: it fits as it is)."""
    return min(1.0, LIMIT / (iw * dpr), LIMIT / (ih * dpr))


def tiles(rect, dpr):
    """A CSS rect [x, y, w, h] -> [(row, col, [x, y, w, h])], each at most LIMIT device px a side (one tile if it fits)."""
    x, y, w, h = rect
    step = LIMIT / dpr
    cols, rows = max(1, -(-w // step)), max(1, -(-h // step))
    out = []
    for r in range(int(rows)):
        for c in range(int(cols)):
            tx, ty = x + c * step, y + r * step
            out.append((r, c, [tx, ty, min(step, x + w - tx), min(step, y + h - ty)]))
    return out


def region(text):
    v = [float(p) for p in text.split(",")]
    if (len(v) != 4 or not all(math.isfinite(x) for x in v)
            or min(v[:2]) < 0 or v[2] <= 0 or v[3] <= 0):
        raise ValueError(f"--region x,y,w,h in CSS px; got {text!r}")
    return v


# ---- the runtime's token: what differs between a Claude builder, a Codex worker and the house ------------------------

def token_facts():
    """This process's token: restricted (Codex's unelevated sandbox makes one), integrity, AppContainer. Read, never
    changed. None for a fact Windows would not give."""
    k32, adv = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("advapi32", use_last_error=True)
    k32.GetCurrentProcess.restype = wt.HANDLE
    adv.OpenProcessToken.argtypes = [wt.HANDLE, wt.DWORD, ctypes.POINTER(wt.HANDLE)]
    adv.IsTokenRestricted.argtypes = [wt.HANDLE]
    adv.GetTokenInformation.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]
    adv.GetSidSubAuthorityCount.restype = ctypes.POINTER(ctypes.c_ubyte)
    adv.GetSidSubAuthority.restype = ctypes.POINTER(wt.DWORD)
    tok = wt.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0008, ctypes.byref(tok)):      # TOKEN_QUERY
        return {"readable": False}
    try:
        out = {"readable": True, "restricted": bool(adv.IsTokenRestricted(tok))}
        n = wt.DWORD()
        buf = (ctypes.c_byte * 256)()
        if adv.GetTokenInformation(tok, 25, buf, 256, ctypes.byref(n)):          # TokenIntegrityLevel
            sid = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
            count = adv.GetSidSubAuthorityCount(ctypes.c_void_p(sid))[0]
            rid = adv.GetSidSubAuthority(ctypes.c_void_p(sid), count - 1)[0]
            out["integrity"] = {0x1000: "low", 0x2000: "medium", 0x2100: "medium-plus", 0x3000: "high", 0x4000: "system"}.get(rid, hex(rid))
        v = wt.DWORD()
        if adv.GetTokenInformation(tok, 29, ctypes.byref(v), 4, ctypes.byref(n)):     # TokenIsAppContainer
            out["appcontainer"] = bool(v.value)
        out["codex_env"] = any(k.startswith("CODEX_") for k in os.environ)
        return out
    finally:
        k32.CloseHandle(tok)


# ---- a copy of the world, served as the keeper serves it ---------------------------------------------------------------

class Copy:
    def __init__(self, world):
        import agora_tmp
        import explore
        import store
        src = LAB / "sessions" / f"{world}.pickle"
        if not src.exists():
            raise SystemExit(f"paint: no world {world!r}")
        desk = explore.load_desk(src)                 # the file plus the log since: the world as it is now
        self.at = len(desk.world.events)
        self.session = f"{world}-paint-{os.getpid()}"
        self.pickle = LAB / "sessions" / f"{self.session}.pickle"
        self.pickle.write_bytes(pickle.dumps(desk))
        store.genesis(desk, self.pickle, why="paint lane copy")
        self.state = Path(agora_tmp.directory("paint-door-"))
        shell = self.state / "desk-shell"
        shutil.copytree(LAB / "desk-shell", shell)
        import sandbox_window as sb
        self.port = sb.free_port()
        self.srv = subprocess.Popen([PY, "door.py", str(self.port), "--no-git", "--state", str(self.state),
                                     "--static", str(shell)], cwd=LAB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.base = f"http://127.0.0.1:{self.port}"
        end = time.time() + 60
        while True:
            try:
                urllib.request.urlopen(self.base + "/lens.html", timeout=2).read()
                break
            except Exception:
                if time.time() > end or self.srv.poll() is not None:
                    self.close()
                    raise SystemExit("paint: the copy's door did not answer")
                time.sleep(0.3)

    def url(self, lens, who):
        return f"{self.base}/lens.html?" + urllib.parse.urlencode(
            {"session": self.session, "as": who, "lens": lens, "view": "painter", "inspect": "0"})

    def close(self):
        self.srv.terminate()
        try:
            self.srv.wait(timeout=10)
        except Exception:
            self.srv.kill()
        time.sleep(3.5)                               # the door's deskd goes within 3 s of the door (screen.py)
        shutil.rmtree(self.state, ignore_errors=True)
        for p in self.pickle.parent.glob(self.pickle.stem + "*"):
            p.unlink(missing_ok=True)


# ---- painting one size ---------------------------------------------------------------------------------------------

DRAWN_JS = "!!document.querySelector('#paint [data-key]') || !!(document.getElementById('status')||{}).textContent"
COUNT_JS = "document.querySelectorAll('#paint [data-key]').length"
STATUS_JS = "(document.getElementById('status')||{}).textContent || ''"
RECT_JS = """(k => { const e = document.querySelector('#paint [data-key="' + CSS.escape(k) + '"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.width, r.height]; })"""


def shoot(c, path, clip=None, scale=1.0):
    from PIL import Image
    args = {"format": "png"}
    if clip:
        args.update(clip={"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3], "scale": scale},
                    captureBeyondViewport=True)
    raw = base64.b64decode(c.call("Page.captureScreenshot", **args)["data"])
    path.write_bytes(raw)
    with Image.open(io.BytesIO(raw)) as im:
        px = list(im.size)
    return {"sha256": hashlib.sha256(raw).hexdigest(), "px": px, "clip": clip, "scale": scale,
            "deliverable": fits(px)}


def local_network_policy():
    """Observed loopback only. Never grant exceptions for browser background traffic."""
    return {"allow_loopback": True, "allow_remote": []}


def paint_one(copy, lens, who, size, crops, regions, root):
    import guard_context
    import sandbox_window as sb
    # what start/close import lazily, imported now (check_native_run_fake: no mid-run __pycache__ writes)
    import sandbox_birth, sandbox_owned, sandbox_job, hud_lifecycle, native_run_verify as nv  # noqa: E401,F401
    run = run_name(size)
    rd = root / run
    rd.mkdir(parents=True)
    name = f"paint-{os.getpid()}-{size}"
    rep = {"lane": "paint (a10672)", "lens": lens, "as": who, "size": size, "world_at": copy.at,
           "runtime": token_facts(), "rows": [{"id": "paint", "outcome": "fail", "shots": []}], "shots": {},
           "network_policy": local_network_policy()}
    adm = guard_context.read()
    rep["admission"] = {"admitted": adm.get("admitted"), "reason": adm.get("reason")}
    if not adm.get("admitted"):
        rep["result"] = "refused before any launch: the house's guard did not admit it; not retried"
        (rd / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
        return run, rep
    guard = sb.Guard(name, f"agora-sandbox-{name}")
    stage = "the guard"
    try:
        with guard:
            stage = "the job"
            with sb.job_scope(name) as scope:
                rep["job"] = dict(scope.descriptor)
                profile = sb.STATE / f"{name}-profile"
                verifier = nv.Verifier({
                    "name": name, "profile_roots": [str(profile)], "scratch_roots": [],
                    "watched_roots": [], **local_network_policy(),
                    "require_engine_report": False,
                }, scope)
                verifier.before()

                def before_cdp(st):
                    for owner in st.get("owners", []):
                        verifier.add_birth({k: owner[k] for k in ("pid", "created", "exe")})
                    verifier.start_sampling(0.1)
                    rep["interaction_gate"] = verifier.gate()
                    if not rep["interaction_gate"]["allow_interaction"]:
                        raise RuntimeError("native-run verifier refused before DevTools; see interaction_gate")

                try:
                    if not guard_context.read().get("admitted"):
                        raise RuntimeError("house admission expired before launch; not retried")
                    stage = "edge"
                    st = sb.open_edge(name, copy.url(lens, who), size, tries=1,
                                      job=scope, before_cdp=before_cdp, local_only=True)
                    rep["viewport"] = st["viewport"]
                    iw, ih, dpr = st["viewport"]
                    stage = "the page's DevTools"
                    c = sb.Cdp(st["port"])
                    try:
                        stage = "the lens drawn"
                        end = time.time() + 30
                        while not c.js(DRAWN_JS):
                            if time.time() > end:
                                raise RuntimeError("the painter drew nothing in 30 s")
                            time.sleep(0.2)
                        last, same, end = -1, 0, time.time() + 15       # steady: the same number of parts for 1 s
                        while same < 5 and time.time() < end:
                            n = c.js(COUNT_JS)
                            same, last = (same + 1, n) if n == last else (0, n)
                            time.sleep(0.2)
                        rep["parts"], rep["status"] = last, c.js(STATUS_JS)
                        if last <= 0:
                            raise RuntimeError("the lens painted no parts; status alone is not a painted lens")
                        stage = "the shots"
                        shots = rep["shots"]
                        shots["01-full.png"] = shoot(c, rd / "01-full.png")
                        k = 2
                        if not shots["01-full.png"]["deliverable"]:
                            s = overview_scale(iw, ih, dpr)
                            shots["02-overview.png"] = shoot(c, rd / "02-overview.png", [0, 0, iw, ih], s)
                            k = 3
                        wanted = [(slug(key), key, None) for key in crops] + \
                                 [(f"region-{'-'.join(str(int(v)) for v in r)}", None, r) for r in regions]
                        for label, key, rect in wanted:
                            if key is not None:
                                rect = c.js(f"{RECT_JS}({json.dumps(key)})")
                                if not rect or rect[2] <= 0 or rect[3] <= 0:
                                    rep.setdefault("missing", []).append(f"{key}: not painted, or of no size")
                                    continue
                            parts = tiles(rect, dpr)
                            for r, col, clip in parts:
                                f = f"{k:02d}-{label}" + (f"-r{r}c{col}" if len(parts) > 1 else "") + ".png"
                                shots[f] = dict(shoot(c, rd / f, clip), part=key, of=rect)
                                k += 1
                    finally:
                        c.close()
                    rep["rows"][0] = {"id": "paint", "outcome": "pass",
                                      "shots": [f for f, s in rep["shots"].items() if s["deliverable"]]}
                    stage = "done"
                finally:
                    verifier.stop_sampling()
                    if sb.state_file(name).exists():
                        rep["cleanup"] = sb.close(name, quiet=True)
                    verifier.after()
                    rep["verification"] = verifier.verdict()
    except BaseException as e:            # SystemExit from open_edge carries its own stage and DevTools state
        from sandbox_receipts import error
        rep["failed_at"], rep["error"] = stage, error(e) if not isinstance(e, SystemExit) else str(e)
    finally:
        if hasattr(guard, "first"):
            code, words = guard.verdict()
            if not guard.first.get("foreground"):
                code, words = 1, "unknown Alex-screen continuity: local foreground unavailable"
            rep["guard"] = [code, words]
        else:
            rep["guard"] = [1, "guard not started"]
        rep["post_admission"] = guard_context.read()
        ok = accepted(rep)
        rep["result"] = ("painted: shots taken, guard untouched, the job's family observed gone" if ok else
                         "not accepted: see failed_at, error, guard and cleanup; not retried")
        if size not in DELIVERABLE:
            rep["delivery"] = f"not deliverable through guarded_artifacts: it admits only {', '.join(DELIVERABLE)}"
        (rd / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")   # last: shots are older
    return run, rep


def deliver(root, run, rep, to, target, prompt, sign):
    """Each deliverable shot of a passed run, as one addressed image comment (guarded_artifacts --send). -> lines."""
    out = []
    if not accepted(rep) or rep["size"] not in DELIVERABLE:
        return [f"{run}: not delivered ({rep.get('result')})"]
    if Path(root).resolve() != DEMO_ROOT.resolve():
        return [f"{run}: not delivered (not the guarded-artifact selector's canonical root)"]
    if os.environ.get("DESKD", "").lower() == "off":
        return [f"{run}: not delivered (Desk delivery is disabled in this runtime; no route override)"]
    for f in rep["rows"][0]["shots"]:
        s = rep["shots"][f]
        words = (prompt or f"Lens {rep['lens']} painted at {rep['size']} CSS px for {rep['as']} (world @{rep['world_at']})") \
            + f"; {f}" + (f", part {s['part']}" if s.get("part") else "") + (f", drawn at scale {s['scale']:.3f}" if s["scale"] != 1 else "")
        r = subprocess.run([PY, str(LAB / "guarded_artifacts.py"), f"{run}/{f}", "--sha256", s["sha256"], "--recipient", to,
                            "--target", target, "--prompt", words, "--as", sign, "--send"],
                           cwd=LAB, capture_output=True, text=True, timeout=120)
        said = (r.stdout.strip().splitlines() or [""])[-1] if r.returncode == 0 else (r.stderr or r.stdout).strip()[-300:]
        out.append(f"{run}/{f}: {'sent' if r.returncode == 0 else 'NOT sent'}: {said}")
        if r.returncode != 0:
            break                         # a refused delivery stops the rest: inspect before trying again
    return out


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("lens")
    a.add_argument("--world", default="frontier")
    a.add_argument("--as", dest="who", default="alex")
    a.add_argument("--sizes", default="1280x800,2560x1440")
    a.add_argument("--crop", action="append", default=[])
    a.add_argument("--region", action="append", default=[], type=region)
    a.add_argument("--root", default=str(DEMO_ROOT))
    a.add_argument("--to")
    a.add_argument("--target")
    a.add_argument("--prompt")
    a.add_argument("--sign", default=os.environ.get("DESK_AS", ""))
    x = a.parse_args(argv)
    sizes = [s.strip().lower() for s in x.sizes.split(",") if s.strip()]
    if not sizes or any(not re.fullmatch(r"\d{3,4}x\d{3,4}", s) for s in sizes):
        a.error("--sizes WxH[,WxH...], e.g. 1280x800,2560x1440")
    if x.to and not (x.target and x.sign):
        a.error("--to needs --target <card> and --sign <who is sending>")
    import guard_context
    admission = guard_context.read()
    if not admission.get("admitted"):
        print("paint: refused before copy/server/browser creation; not retried: "
              + str(admission.get("reason", "house guard admission unavailable")))
        return 1
    root = Path(x.root)
    copy = Copy(x.world)
    results = []
    try:
        for size in sizes:
            run, rep = paint_one(copy, x.lens, x.who, size, x.crop, x.region, root)
            results.append((run, rep))
            print(f"{root / run}: {rep['result']}" + (f" (failed at {rep['failed_at']}: {rep['error']})" if rep.get("error") else ""))
            for f, s in rep["shots"].items():
                print(f"  {f} {s['px'][0]}x{s['px'][1]}{'' if s['deliverable'] else ' (evidence only: over 2048)'} {s['sha256'][:12]}")
            if not accepted(rep):
                break  # a concrete failure ends this request, including other sizes
    finally:
        copy.close()
    deliveries_ok = True
    if x.to:
        for run, rep in results:
            for line in deliver(root, run, rep, x.to, x.target, x.prompt, x.sign):
                print(line)
                if "NOT sent" in line or "not delivered" in line:
                    deliveries_ok = False
    return 0 if deliveries_ok and len(results) == len(sizes) and all(accepted(r) for _, r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
