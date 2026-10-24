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
            self._agora_guard_refs = (frame_created, any_frame_navigation, resource, refs)
        original(self, sender, args)
        if args.IsSuccess:
            sender.CoreWebView2.Settings.AreDefaultScriptDialogsEnabled = False

    EdgeChrome.on_webview_ready = ready
    EdgeChrome._agora_widget_guard = True
