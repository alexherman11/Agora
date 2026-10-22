"""Bounded offline native WebView2 probe. Only on its named hidden desktop.

No pywebview bridge, debug port, public navigation, profile import or process kill.
The parent supplies a fresh receipt directory and keeps all failure evidence.
"""

import ctypes
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path


def main():
    folder = Path(sys.argv[1]).resolve()
    folder.relative_to(Path(__file__).resolve().parents[1] / ".tmp-agora")
    name = sys.argv[2]
    if not name.startswith("agora-sandbox-admit-"):
        raise ValueError("named admission desktop required")
    user, kernel = ctypes.windll.user32, ctypes.windll.kernel32
    user.GetThreadDesktop.restype = ctypes.c_void_p
    user.GetUserObjectInformationW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
    ]
    desktop = user.GetThreadDesktop(kernel.GetCurrentThreadId())
    value, needed = ctypes.create_unicode_buffer(256), ctypes.c_uint()
    if not user.GetUserObjectInformationW(
        desktop, 2, value, ctypes.sizeof(value), ctypes.byref(needed)
    ):
        raise RuntimeError("desktop identity unavailable")
    if value.value != name:
        raise RuntimeError("wrong desktop; no window created")
    started = time.monotonic()
    report = {"desktop": name, "pid": os.getpid(), "events": [], "public_navigation": False}

    def record(phase, **fields):
        report["phase"] = phase
        report["events"].append(
            {"phase": phase, "seconds": round(time.monotonic() - started, 3), **fields}
        )
        temp = folder / "receipt.pending"
        temp.write_text(json.dumps(report, indent=2), encoding="utf-8")
        temp.replace(folder / "receipt.json")

    record("importing")
    import clr

    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    lib = Path(importlib.metadata.distribution("pywebview").locate_file("webview/lib"))
    clr.AddReference(str(lib / "Microsoft.Web.WebView2.Core.dll"))
    clr.AddReference(str(lib / "Microsoft.Web.WebView2.WinForms.dll"))
    from Microsoft.Web.WebView2.Core import (
        CoreWebView2WebResourceContext,
        CoreWebView2WebResourceRequestSourceKinds,
    )
    from Microsoft.Web.WebView2.WinForms import CoreWebView2CreationProperties, WebView2
    from System import Action, String
    from System.Threading import ApartmentState, Thread, ThreadStart
    from System.Threading.Tasks import Task, TaskScheduler
    from System.Windows.Forms import Application, DockStyle, Form, Timer

    def run():
        form, view = None, None
        try:
            form = Form()
            form.Text = "Agora offline admission probe"
            form.Width, form.Height = 900, 650
            view = WebView2()
            props = CoreWebView2CreationProperties()
            props.UserDataFolder = str(folder / "profile")
            props.IsInPrivateModeEnabled = True
            view.CreationProperties = props
            view.Dock = DockStyle.Fill
            form.Controls.Add(view)
            deadline = Timer()
            deadline.Interval = 25000

            def expired(*_):
                record("deadline_fired", initialized=bool(view.CoreWebView2))
                deadline.Stop()
                form.Close()

            deadline.Tick += expired

            def ready(_, args):
                if not args.IsSuccess:
                    exc = args.InitializationException
                    record(
                        "initialization_failed",
                        hresult=exc.HResult,
                        error_type=str(exc.GetType().FullName),
                    )
                    deadline.Stop()
                    form.Close()
                    return
                core = view.CoreWebView2
                record("initialized", engine=str(core.Environment.BrowserVersionString))
                core.Environment.BrowserProcessExited += lambda _, e: record(
                    "browser_exited", kind=str(e.BrowserProcessExitKind), pid=e.BrowserProcessId
                )
                core.ProcessFailed += lambda _, e: record(
                    "process_failed", kind=str(e.ProcessFailedKind)
                )
                settings = core.Settings
                # Positive control first: the native event counters must actually work.
                # No host object or command handler exists in either phase.
                settings.IsWebMessageEnabled = True
                settings.AreHostObjectsAllowed = False
                settings.AreDevToolsEnabled = False
                settings.IsGeneralAutofillEnabled = False
                settings.IsPasswordAutosaveEnabled = False
                settings.AreDefaultContextMenusEnabled = False
                messages = []
                core.WebMessageReceived += lambda *_: messages.append("top")

                def frame_created(_, e):
                    e.Frame.WebMessageReceived += lambda *_: messages.append("child")

                core.FrameCreated += frame_created
                core.AddWebResourceRequestedFilter(
                    "*",
                    CoreWebView2WebResourceContext.All,
                    CoreWebView2WebResourceRequestSourceKinds.All,
                )

                def deny(_, e):
                    e.Response = core.Environment.CreateWebResourceResponse(
                        None, 403, "Offline probe", ""
                    )

                core.WebResourceRequested += deny
                mode = ["positive_control"]
                html = (
                    "<!doctype html><title>Offline admission</title>"
                    "<h1>Offline native WebView2</h1>"
                    "<iframe srcdoc='<p>Offline child</p>'></iframe>"
                )
                record(
                    "offline_policy",
                    messages=settings.IsWebMessageEnabled,
                    host_objects=settings.AreHostObjectsAllowed,
                )

                def loaded(_, e):
                    record(
                        "navigation_completed", success=e.IsSuccess, status=str(e.WebErrorStatus)
                    )
                    if not e.IsSuccess:
                        form.Close()
                        return
                    scheduler = TaskScheduler.FromCurrentSynchronizationContext()
                    task = core.ExecuteScriptAsync("""(() => {
                      const child=document.querySelector('iframe').contentWindow;
                      function attempt(w) {
                        try { w.chrome.webview.postMessage('offline-canary'); return 'sent'; }
                        catch(e) { return 'threw'; }
                      }
                      return JSON.stringify({title:document.title,
                        topBridge:typeof window.pywebview, childBridge:typeof child.pywebview,
                        topMessage:attempt(window), childMessage:attempt(child),
                        childReady:child.document.readyState});
                    })()""")

                    def checked(answer):
                        try:
                            result = json.loads(json.loads(str(answer.Result)))
                            record("evaluated", mode=mode[0], result=result)
                            observation = Timer()
                            observation.Interval = 500

                            def finish(*_):
                                observation.Stop()
                                record("message_delivery", mode=mode[0], received=list(messages))
                                if mode[0] == "positive_control":
                                    settings.IsWebMessageEnabled = False
                                    mode[0] = "disabled"
                                    messages.clear()
                                    record(
                                        "offline_policy",
                                        messages=settings.IsWebMessageEnabled,
                                        host_objects=settings.AreHostObjectsAllowed,
                                    )
                                    core.NavigateToString(html)
                                else:
                                    deadline.Stop()
                                    form.Close()

                            observation.Tick += finish
                            observation.Start()
                        except Exception as exc:
                            record("evaluation_failed", error_type=type(exc).__name__)
                            deadline.Stop()
                            form.Close()

                    task.ContinueWith(Action[Task[String]](checked), scheduler)

                core.NavigationCompleted += loaded
                core.NavigateToString(html)

            view.CoreWebView2InitializationCompleted += ready

            def shown(*_):
                record("shown", handle_created=view.IsHandleCreated)
                deadline.Start()
                record("initializing")
                view.EnsureCoreWebView2Async(None)

            form.Shown += shown
            record("message_loop")
            Application.Run(form)
            deadline.Stop()
            record("form_closed")
        except Exception as exc:
            record(
                "native_exception",
                error_type=type(exc).__name__,
                hresult=getattr(exc, "HResult", None),
            )
        finally:
            if view is not None:
                view.Dispose()
            if form is not None:
                form.Dispose()
            record("disposed")

    thread = Thread(ThreadStart(run))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()
    thread.Join()
    record("child_exit")


if __name__ == "__main__":
    main()
