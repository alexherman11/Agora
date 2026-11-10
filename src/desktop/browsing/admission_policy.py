"""Fail-closed OFFLINE WebView2 event policy; no public navigation capability."""


def configure(settings, *, positive_control=False):
    """No objects/privileged handlers are registered by this fixture."""
    settings.IsWebMessageEnabled = positive_control
    settings.AreHostObjectsAllowed = False
    settings.AreDevToolsEnabled = False
    settings.IsGeneralAutofillEnabled = False
    settings.IsPasswordAutosaveEnabled = False
    settings.AreDefaultContextMenusEnabled = False
    settings.AreBrowserAcceleratorKeysEnabled = False
    settings.AreDefaultScriptDialogsEnabled = False


def install(core, denied, deny_permission, contexts, sources):
    """Attach actual native event handlers; also exercised with fake event args.

    Missing engine APIs fail initialization rather than weakening containment.
    The only content entry is the trusted fixture's NavigateToString.
    """
    def navigation(_, event):
        if event.Uri not in ("about:blank", "about:srcdoc"):
            event.Cancel = True
            denied("navigation")

    def resource(_, event):
        event.Response = core.Environment.CreateWebResourceResponse(
            None, 403, "Offline probe", "")
        denied("resource")

    def popup(_, event):
        event.Handled = True
        denied("popup")

    def permission(_, event):
        event.State = deny_permission
        event.Handled = True
        denied("permission")

    def download(_, event):
        event.Cancel = True
        denied("download")

    def external(_, event):
        event.Cancel = True
        denied("external_scheme")

    core.NavigationStarting += navigation
    core.FrameNavigationStarting += navigation
    core.AddWebResourceRequestedFilter("*", contexts, sources)
    core.WebResourceRequested += resource
    core.NewWindowRequested += popup
    core.PermissionRequested += permission
    core.DownloadStarting += download
    core.LaunchingExternalUriScheme += external
