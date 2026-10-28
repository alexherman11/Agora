"""Keep each native window's private cookies independent.

Pinned pywebview clears all profile cookies in EdgeChrome.on_webview_ready.
Its default shared profile lets a newly initialized window erase another
window's sign-in between /dev/signin and /desk/window-origin (or later).
Use WebView2's named profiles within the existing user-data folder. Private
mode, the cookie-only sign-in chain and the native widget guard stay intact.
"""
from uuid import uuid4


def install():
    """Install before constructing any EdgeChrome, including the hidden anchor."""
    from webview.platforms import edgechromium

    if getattr(edgechromium, "_agora_window_profiles", False):
        return
    creation_properties = edgechromium.CoreWebView2CreationProperties

    def independent_properties():
        props = creation_properties()
        # Random per construction, including reopen: no profile is reused by a
        # second live view. One environment/browser can still serve all profiles.
        props.ProfileName = "agora-" + uuid4().hex
        return props

    edgechromium.CoreWebView2CreationProperties = independent_properties
    edgechromium._agora_window_profiles = True
