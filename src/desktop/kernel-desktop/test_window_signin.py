"""Real private WebView2 startup/restart test on a guarded hidden desktop.

No shell reservations, visible windows, user sessions or live world writes.
The late blank view deterministically reproduces pywebview's cookie erasure.
"""
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from uuid import uuid4

HERE = Path(__file__).resolve().parent
PYTHON = r"C:\Projects\Agora4\.venv\Scripts\python.exe"


def child(result_path, shared=False):
    def progress(stage):
        Path(result_path).with_suffix(".progress").write_text(stage, encoding="utf-8")

    progress("imports")
    import webview
    import window_profiles
    from kd_window import GuiScreen
    from test_kdesk import Desk
    from test_stream_windows import window_url

    # A negative control uses the pinned runtime's original shared profile.
    if shared:
        window_profiles.install = lambda: None
    progress("disposable world startup")
    d = Desk()
    progress("native startup")
    screen = GuiScreen(None)
    result = {"rounds": [], "ok": False}
    opened = []

    def inspect():
        try:
            progress("creating window intent")
            # Same persisted window intent across module restarts.
            rows = []
            for view in ("shell-top", "shell-dock", "help", "lines"):
                out = d.say(f'make kind=window shows={view} name="Signin fixture {view}"')
                assert out["ok"], out["text"]
                rows.append((out["made"][0], view))
            for round_number in range(3):
                progress(f"round {round_number}: native windows")
                if round_number:
                    mid = next(m for m in d.k.things("module") if d.k.state.get(m, "name") == "window")
                    assert d.say("off window")["ok"]
                    d.wait(lambda: not d.host.running(mid))
                    assert d.say("undo")["ok"]
                    d.wait(lambda: all(wid in {w["id"] for w in d.windows()} for wid, _ in rows))
                current = []
                for wid, view in rows:
                    page = {"shell-top": "shell/top", "shell-dock": "shell/dock"}.get(view, view)
                    url = window_url(d.url, d.entry.token("alex"), wid,
                                     f"/desk/{page}.html?win={wid}")
                    win = webview.create_window("Agora signin fixture", url, hidden=True)
                    opened.append(win)
                    current.append(win)

                def signed(win):
                    if not win.events.loaded.is_set():
                        return False
                    if not win.evaluate_js("typeof KD !== 'undefined'"):
                        return False
                    done, values = threading.Event(), []
                    def answer(value):
                        values.append(value)
                        done.set()
                    win.evaluate_js("KD.see('who').then(r=>r.ok===true)", callback=answer)
                    return done.wait(5) and values == [True]

                for win in current:
                    d.wait(lambda: signed(win), 30)
                progress(f"round {round_number}: late blank view")
                # A late native view used to delete every already-open view's
                # cookies, even with no sign-in navigation of its own.
                late = webview.create_window("Agora signin fixture late", html="<p>late view</p>",
                                             hidden=True)
                opened.append(late)
                assert late.events.loaded.wait(20), "late view did not initialize"
                survived = [signed(win) for win in current]
                assert all(survived), "a new view erased existing windows' sign-in"
                profiles = [str(w.native.browser.webview.CoreWebView2.Profile.ProfileName)
                            for w in [screen.anchor, *current, late]]
                assert len(set(profiles)) == len(profiles), "native views share a cookie profile"
                assert all(not bool(w.native.Visible) for w in opened), "fixture became visible"
                assert all(not w.evaluate_js("document.cookie.includes('agora_session')")
                           for w in current), "session cookie is script-readable"
                result["rounds"].append({"round": round_number, "signed": len(current),
                                         "survived_late_view": sum(survived),
                                         "private": all(bool(w.native.browser.webview.CoreWebView2.Profile.IsInPrivateModeEnabled)
                                                        for w in current)})
                for win in [*current, late]:
                    win.destroy()
                opened.clear()
            result["ok"] = all(r["private"] for r in result["rounds"])
        except Exception as exc:
            # Never serialize URLs or tokens in failure evidence.
            result["error"] = type(exc).__name__ + ": " + str(exc) if isinstance(exc, AssertionError) else type(exc).__name__
        finally:
            progress("closing native fixture")
            for win in opened:
                win.destroy()
            screen.anchor.destroy()

    try:
        screen.start(inspect)
    finally:
        progress("closing disposable world")
        d.close()
        Path(result_path).write_text(json.dumps(result, indent=2), encoding="utf-8")


class WindowSigninTest(unittest.TestCase):
    def test_private_windows_sign_in_across_module_restarts(self):
        sys.path.insert(0, str(HERE.parent))
        import sandbox_window as sb
        name = "signin-" + uuid4().hex[:10]
        result_path = sb.STATE / (name + "-result.json")
        with sb.Guard(name, "Agora signin fixture") as guard:
            sb.run_hidden(name, [PYTHON, str(Path(__file__).resolve()), "--child", str(result_path)])
            end = time.monotonic() + 150
            while not result_path.exists() and time.monotonic() < end:
                time.sleep(.2)
        self.assertTrue(result_path.exists(), "hidden fixture timed out; retained ownership receipt")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertFalse(any(note[2] for note in guard.notes), str(guard.notes))
        print("Hidden WebView2 sign-in: " + json.dumps(result), flush=True)
        self.assertTrue(result["ok"], result)
        self.assertEqual(3, len(result["rounds"]))


if __name__ == "__main__":
    if "--child" in sys.argv:
        result_path = sys.argv[sys.argv.index("--child") + 1]
        try:
            child(result_path, "--shared" in sys.argv)
        except Exception as exc:
            Path(result_path).write_text(json.dumps({"ok": False, "rounds": [],
                                                    "error": type(exc).__name__}), encoding="utf-8")
    else:
        unittest.main()
