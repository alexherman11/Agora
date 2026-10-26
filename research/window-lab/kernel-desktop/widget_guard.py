"""Native WebView2 guard installed before any desktop page loads.

CSP covers fetch destinations, not self navigation. Untrusted frames may only
navigate to their initial srcdoc; no popups, downloads, native messages or dialogs.
The guard is mandatory: initialization fails closed if the APIs are unavailable.
"""


def install():
    from webview.platforms.edgechromium import EdgeChrome
    if getattr(EdgeChrome, '_agora_widget_guard', False):
        return
    original = EdgeChrome.on_webview_ready
    original_notify=EdgeChrome.on_script_notify
    def notify(self,sender,event):
        import json
        try:
            value=json.loads(str(event.WebMessageAsJson))
            if isinstance(value,str):value=json.loads(value)
            if isinstance(value,dict) and value.get('agora')=='recover-widget-renderer':return
        except Exception:pass
        original_notify(self,sender,event)
    EdgeChrome.on_script_notify=notify

    def ready(self, sender, args):
        if args.IsSuccess:
            core = sender.CoreWebView2
            refs = {}
            self._agora_widget_denials = []

            def resource(sender, event):
                from urllib.parse import urlsplit
                from System.IO import MemoryStream
                uri=urlsplit(str(event.Request.Uri))
                headers=event.Request.Headers
                if uri.scheme=='http' and uri.hostname=='127.0.0.1' and uri.path.startswith('/desk/widget/'):
                    import os
                    key=os.environ.get('AGORA_WIDGET_HOST_KEY')
                    if key:headers.SetHeader('X-Agora-Widget-Host',key)
                def header(name):
                    return str(headers.GetHeader(name)) if headers.Contains(name) else ''
                # All desktop resources are local. Opaque-origin navigations
                # carry cross-site fetch metadata, unlike trusted lens frames.
                denied=(str(event.ResourceContext)=='Document' and str(event.Request.Uri) in self._agora_widget_denials) or (uri.scheme in ('http','https') and uri.hostname!='127.0.0.1') or (
                    header('Sec-Fetch-Dest')=='iframe' and
                    (header('Sec-Fetch-Site') not in ('same-origin','same-site') or
                     uri.path not in ('/lens.html','/desk/widget.html')))
                if denied:
                    event.Response=core.Environment.CreateWebResourceResponse(MemoryStream(),403,'Widget network denied','Content-Type: text/plain')
                    self._agora_widget_denials.append(str(event.Request.Uri))

            from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext, CoreWebView2WebResourceRequestSourceKinds
            # The old two-argument overload does NOT subscribe to iframe traffic.
            core.AddWebResourceRequestedFilter('*',CoreWebView2WebResourceContext.All,
                                               CoreWebView2WebResourceRequestSourceKinds.Document)
            core.WebResourceRequested += resource

            def any_frame_navigation(sender, event):
                from urllib.parse import urlsplit
                uri=str(event.Uri)
                parsed=urlsplit(uri)
                # Trusted lens/slot frames have these exact local addresses.
                # The per-frame guard below is stricter for a widget frame.
                allowed=(uri in ('about:blank','about:srcdoc') or
                         (parsed.scheme=='http' and parsed.hostname=='127.0.0.1' and
                          parsed.path in ('/lens.html','/desk/widget.html')))
                if not allowed:
                    event.Cancel=True
                    self._agora_widget_denials.append(uri)

            core.FrameNavigationStarting += any_frame_navigation

            def frame_created(sender, event):
                frame = event.Frame
                first = [True]
                opaque = [str(frame.Name) == 'agora-widget']

                def navigate(sender, event):
                    uri = str(event.Uri)
                    opaque[0] = opaque[0] or str(frame.Name) == 'agora-widget' or uri == 'about:srcdoc'
                    if not opaque[0]:
                        return  # a trusted lens or slot host frame
                    initial = first[0] and uri in ('about:srcdoc', 'about:blank')
                    if uri != 'about:blank':
                        first[0] = False
                    event.Cancel = not initial
                    if not initial:
                        self._agora_widget_denials.append(str(event.Uri))

                def message(sender, event):
                    # pywebview's native message handler belongs to top-level
                    # chrome. It is never registered on this frame.
                    pass

                frame.NavigationStarting += navigate
                if hasattr(frame, 'FrameCreated'):
                    frame.FrameCreated += frame_created  # a bar slot's nested sandbox
                key=id(frame)
                def destroyed(sender,event):
                    refs.pop(key,None)
                frame.Destroyed += destroyed
                # Handles to the frame are kept alive along with callbacks.
                refs[key]=(frame, navigate, message, destroyed)

            core.FrameCreated += frame_created
            core.Settings.AreDefaultScriptDialogsEnabled = False
            self._agora_renderer_failures=[]
            def process_failed(sender,event):
                import time
                kind=str(event.ProcessFailedKind)
                if kind=='FrameRenderProcessExited':
                    # The parent and its watchdog are alive. Let them attribute
                    # the failure to an active part, without reloading bars.
                    core.ExecuteScriptAsync("dispatchEvent(new Event('agora-frame-failed'))")
                    return
                if kind not in ('RenderProcessExited','RenderProcessUnresponsive'):return
                now=time.monotonic()
                self._agora_renderer_failures[:]=[t for t in self._agora_renderer_failures if now-t<60]
                self._agora_renderer_failures.append(now)
                from gaming_gate import reasons
                if reasons():return  # defer live navigation while the screen gate is closed
                if len(self._agora_renderer_failures)==1:
                    core.Reload()
                else:
                    # A bounded restart, then a trusted calm replacement, never
                    # an endless crash/reload loop or another window's process.
                    core.NavigateToString('<!doctype html><meta charset="utf-8"><body style="background:#FAF9F6;color:#35433D;font:14px Segoe UI;padding:24px"><strong>This part stopped</strong><p>This window could not keep responding. Close and reopen it to try again.</p>')
            core.ProcessFailed += process_failed
            recovery_tasks=[]
            def recovery_message(sender,event):
                import json
                from urllib.parse import urlsplit,parse_qs
                try:
                    request=json.loads(str(event.TryGetWebMessageAsString()))
                except Exception:return  # pywebview's ordinary messages
                if not isinstance(request,dict) or request.get('agora')!='recover-widget-renderer':return
                source=urlsplit(str(event.Source))
                if source.scheme!='http' or source.hostname!='127.0.0.1' or source.path!='/desk/widget.html':return
                expected=str(event.Source)
                def reply(ok,error=''):
                    detail=json.dumps(dict(ok=ok,error=error))
                    core.ExecuteScriptAsync("dispatchEvent(new CustomEvent('agora-renderer-recovered',{detail:"+detail+"}))")
                task=core.Environment.GetProcessExtendedInfosAsync()
                from System import Action
                def finish():
                    try:
                        matches=[]
                        for process in task.Result:
                            if str(process.ProcessInfo.Kind)!='Renderer':continue
                            frames=list(process.AssociatedFrameInfos)
                            def mine(frame):
                                parent=frame.ParentFrameInfo
                                return str(frame.Name)=='agora-widget' and parent is not None and str(parent.Source)==expected
                            if frames and any(mine(frame) for frame in frames):
                                if not all(mine(frame) for frame in frames):
                                    reply(False,'Renderer is shared with another view; no process was killed');return
                                matches.append(int(process.ProcessInfo.ProcessId))
                        if len(matches)!=1:
                            reply(False,'No uniquely owned widget renderer; no process was killed');return
                        from gaming_gate import reasons
                        if reasons():reply(False,'Screen gate is closed; recovery is deferred');return
                        from System.Diagnostics import Process as NativeProcess
                        NativeProcess.GetProcessById(matches[0]).Kill()
                        reply(True)
                    except Exception as exc:reply(False,str(exc))
                    finally:
                        if task in recovery_tasks:recovery_tasks.remove(task)
                recovery_tasks.append(task)
                task.GetAwaiter().OnCompleted(Action(lambda:self.webview.BeginInvoke(Action(finish))))
            core.WebMessageReceived += recovery_message
            self._agora_guard_refs = (frame_created, any_frame_navigation, resource, refs, process_failed,recovery_message,recovery_tasks)
        original(self, sender, args)
        if args.IsSuccess:
            sender.CoreWebView2.Settings.AreDefaultScriptDialogsEnabled = False

    EdgeChrome.on_webview_ready = ready
    EdgeChrome._agora_widget_guard = True
