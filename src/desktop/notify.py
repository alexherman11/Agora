"""notify.py: a Windows notification (a toast) on Alex's PC, from the desk (a5824). 16 Oct 2026.

    python notify.py <words>                 show one toast now: title Agora, the words, silent
    python notify.py --sound <words>         the same with the default notification sound
    python notify.py pending <world>         what the house would toast now from the world's Notifications sent chat
    python notify.py history                 the toasts Windows still holds in his notification centre (shows nothing)

How: Windows PowerShell 5.1 (in every Windows 10 and 11) loads the WinRT toast classes and shows one toast. Nothing is
installed and nothing is elevated; no registry key is written. A toast must name an installed app, and an unregistered
name shows nothing, so it is shown as Windows PowerShell's (APP below): Windows draws "Windows PowerShell" small at its
top, then the title "Agora" in bold, then the words. A toast never takes the focus or a key press. The words reach
PowerShell as an environment variable, never as part of the script, so nothing in them is run.

Who sends one:
  - a lens or the home base: the host verb `notify <words>` (host_verbs.py), at once, from hud.py's process;
  - anyone in the world, a card or a rule: the house verb `notify <words>` (houseverbs.py) adds a line to the chat
    with prop role=notifications ("Notifications sent", in the Board room), so every send is a record (who and when
    are the line's event: `examine <m id>`); the house (house.py, for the world `frontier` under keeper only) toasts
    each new line within a pass (~2 s). Words that begin with `!` ask for the sound (the ! is not shown).

What it cannot do, plainly: Focus Assist / Do not disturb, a full-screen program or game, a locked screen and
presentation mode hold the banner back; the toast still goes to the notification centre, unseen until he opens it.
show() says so for the last four (state(): Windows' own answer), but Windows does not say whether Do not disturb is on,
so 'shown' means only that nothing Windows reports was holding it. Notifications turned off for Windows PowerShell in
Settings > System > Notifications show nowhere, and nothing here can tell. `history` lists what the centre holds.
Off switch: the chat's prop toast=off (world), or AGORA_TOASTS=off in the house's environment.
"""
import base64
import os
import subprocess
import sys

TITLE = "Agora"
APP = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
FRESH = 600          # the house toasts a line only this many seconds after it was said: a house that was down for an
#                      hour does not pour an hour of old notices on him (they are still in the chat)
SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$t = [Security.SecurityElement]::Escape($env:AGORA_TOAST_TITLE)
$w = [Security.SecurityElement]::Escape($env:AGORA_TOAST_WORDS)
$b = ''
if ($env:AGORA_TOAST_BY) { $b = '<text placement="attribution">' + [Security.SecurityElement]::Escape($env:AGORA_TOAST_BY) + '</text>' }
$a = '<audio silent="true"/>'
if ($env:AGORA_TOAST_SOUND -eq '1') { $a = '<audio src="ms-winsoundevent:Notification.Default"/>' }
$x = New-Object Windows.Data.Xml.Dom.XmlDocument
$x.LoadXml("<toast><visual><binding template=""ToastGeneric""><text>$t</text><text>$w</text>$b</binding></visual>$a</toast>")
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:AGORA_TOAST_APP).Show([Windows.UI.Notifications.ToastNotification]::new($x))
'shown'
"""
HISTORY = r"""
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
foreach ($n in [Windows.UI.Notifications.ToastNotificationManager]::History.GetHistory($env:AGORA_TOAST_APP)) {
  $t = @($n.Content.GetElementsByTagName('text') | ForEach-Object { $_.InnerText }) -join ' | '
  "$($n.ExpirationTime) $t"
}
"""


QUNS = {1: "held back: the screen is locked or the screen saver runs", 2: "held back: a full-screen program has the screen",
        3: "held back: a full-screen game (Direct3D) runs", 4: "held back: presentation mode", 5: "shown",
        6: "held back: quiet time (the first hour after Windows was set up)", 7: "held back: a full-screen app"}


def state():
    """What Windows says it would do with a banner now (SHQueryUserNotificationState; read only, shows nothing).
    -> 'shown' or 'held back: <why>'. Focus Assist / Do not disturb is NOT in this answer: Windows does not say."""
    import ctypes
    n = ctypes.c_int(0)
    if ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(n)) != 0:
        return "unknown"
    return QUNS.get(n.value, f"unknown ({n.value})")


def _powershell(script, env, timeout=20):
    enc = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                           "-EncodedCommand", enc], env={**os.environ, **env}, capture_output=True, text=True,
                          timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def history():
    """The toasts shown as APP that Windows still holds in the notification centre (each: when it expires, then its
    texts), read without showing anything. A toast he dismissed, or one Windows dropped, is not there."""
    r = _powershell(HISTORY, {"AGORA_TOAST_APP": APP})
    if r.returncode != 0:
        raise RuntimeError((r.stderr or f"powershell exited {r.returncode}").strip().splitlines()[0][:200])
    return [line for line in r.stdout.splitlines() if line.strip()]


def words_of(text):
    """-> (words, sound): the words as said, outer quotes off (`notify "done"` arrives as "done"), a leading ! asks
    for the sound."""
    w = str(text or "").strip()
    if len(w) >= 2 and w[0] == w[-1] and w[0] in "\"'":
        w = w[1:-1].strip()
    sound = w.startswith("!")
    return (w[1:].strip() if sound else w), sound


def show(words, sound=False, by="", title=TITLE, timeout=20):
    """Show one toast (`by`, when given, is its small grey last line: 'from jeff'). -> "shown" when Windows took it and
    would show a banner, or 'in the notification centre only; ...' when it says it holds banners back now (state());
    raises RuntimeError with PowerShell's words when it did not take it."""
    words = " ".join(str(words).split())[:300]
    if not words:
        raise RuntimeError("a notification needs words")
    r = _powershell(SCRIPT, {"AGORA_TOAST_TITLE": title, "AGORA_TOAST_WORDS": words, "AGORA_TOAST_APP": APP,
                             "AGORA_TOAST_SOUND": "1" if sound else "0", "AGORA_TOAST_BY": f"from {by}" if by else ""},
                    timeout)
    if r.returncode != 0 or "shown" not in r.stdout:
        raise RuntimeError((r.stderr or r.stdout or f"powershell exited {r.returncode}").strip().splitlines()[0][:200])
    now = state()
    return "shown" if now in ("shown", "unknown") else f"in the notification centre only; the banner was {now}"


# -- the record: the chat with prop role=notifications, read from a loaded world (house.py holds one each pass)
def chat(w):
    """-> the subject of the notifications chat, or None."""
    for s in w.subjects.values():
        if (s.get("props") or {}).get("role") == "notifications" and w.appearances_of(s["id"]):
            return s
    return None


def pending(w, done, now_iso, fresh=FRESH):
    """The lines of the notifications chat not yet toasted -> [(line id, who, words, sound)]: each line an append made
    (the chat's own opening text is not a notice), not in `done`, said within `fresh` seconds of now_iso."""
    from datetime import datetime
    s = chat(w)
    if s is None or str((s.get("props") or {}).get("toast", "")).lower() == "off":
        return []
    now = datetime.fromisoformat(now_iso)
    out = []
    for line in s.get("lines") or ():
        if line["id"] in done:
            continue
        e = w.event_by_id(line.get("ev"))
        if not e or "append" not in (e.get("args") or {}):          # an append is stored as an edit with append=
            continue
        try:
            age = (now - datetime.fromisoformat(e.get("at"))).total_seconds()
        except (TypeError, ValueError):
            continue
        if age > fresh:
            continue
        who = str(e.get("by") or "someone").split("/")[0]
        text = line["text"]
        head = text.split(":", 1)
        if len(head) == 2 and head[0].strip().lower() == who.lower():     # the world signs it "Who: words"
            text = head[1]
        words, sound = words_of(text)
        if words:
            out.append((line["id"], who, words, sound))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["pending"]:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "text-desk", "notation"))
        import export_docs
        from datetime import datetime
        world = a[1] if len(a) > 1 else "frontier"
        for p in pending(export_docs.load(world).world, set(), datetime.now().isoformat(timespec="seconds")):
            print(p)
    elif a == ["state"]:
        print(state())
    elif a == ["history"]:
        print("\n".join(history()) or "(none held)")
    elif a:
        sound = a[0] == "--sound"
        print(show(" ".join(a[1:] if sound else a), sound=sound))
    else:
        sys.exit(__doc__.split("\n\n")[0])
