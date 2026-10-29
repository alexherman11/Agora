# Blank Agora windows, 28 Oct 2026

> **Corrected 20:10 (Claude): the cause was not a starved machine.** It was the "come back tucked" path in
> `kd_window.py`. See "Cause, found" below. The memory and orphan-browser findings stand as a separate leak.

## Cause, found (ran, 20:00)

A window tucked before a restart is shown by Win32 `ShowWindow(SW_SHOWMINNOACTIVE)`, past WinForms. WinForms
still thinks the form is hidden, so the WebView2 control keeps its controller `IsVisible = false`. Restored later,
the window is there but the page is hidden: a blank cream box (the form's `background_color`).

- Live: blank JEFF chat had its `Chrome_WidgetWin_0` child hidden; the top bar and dock (shown normally) had it
  visible. Every tucked window had it hidden.
- Sandbox (off-screen tool window, no taskbar): shown tucked, then restored → view hidden. Shown normally,
  minimised, restored → view visible. With the fix at tuck time: view visible after restore → tuck → restore.
- Showing the hidden child windows from outside did not make them paint: the controller is what counts.
- Fix: `_page_visible(win)` sets the WebView2 control's private `_coreWebView2Controller.IsVisible = True` on the
  GUI thread, right after the tucked show. Applied live with `off window` / `on window` at 20:10: all 12 windows'
  views visible, JEFF chat, Lines and Component gallery drawn on screen.
- It uses a private field of `Microsoft.Web.WebView2.WinForms`; a pywebview or WebView2 update could rename it.
  Then it logs `page visible: ...` in the window module's stderr and the old blank comes back.

*Claude, from Alex's ask: "agora windows are often coming up as blank white boxes? cant tell why".*

## What was seen (ran)

- 12:42: two Agora windows on screen were plain cream (`#F6F3EC`, the window's own `background_color`), with no
  title strip. The page inside had never painted.
- The window process then (pid 135668, started 12:16) did not answer: a script that read window titles with
  `GetWindowTextW` (which messages each window) hung past 120 s. A version that does not message windows ran fine.
  Not proven which window was hung.
- 12:46 the whole desktop restarted (kdesk.log; one start just before it failed with
  `ImportError: cannot import name 'is_' from 'kernel.kinds'`). After it, every window drew: map and Writing fine
  at 12:47.
- 42 headless Chromes from `state\edge-kdesk-*` were still running, every one with its owner gone: 452 processes,
  about 11.8 GB. 41 came from `test_shell_components.py` (its flags), one from a widget overlay on 26 Oct. Free
  memory was 3.7 GB of 32 GB. After ending them: 7.0 GB free.
- kdesk.log earlier today also has `WinError 10055` (Windows out of socket buffers) in the window door, and 2,413
  TIME_WAIT sockets on kdesk's own module ports at 12:4x.

## Cause, as first guessed (12:50, superseded above)

**read/imagined:** a WebView2 page that never paints, while its window process stops answering, fits a starved
machine (memory, socket buffers) better than a page bug: the same pages drew at once after the restart. Not proven.
What would settle it: the next blank window, checked for (a) `IsHungAppWindow` on it, (b) free memory, (c) new
orphan Chromes, before anything restarts.

## Fixed

- `widget_browser.Browser` starts Chrome suspended, puts it in a Windows job with kill-on-close, then resumes it.
  The browser now ends with whatever started it, however that ends. **ran:** owner killed hard, Chrome processes
  13 → 0; `test_shell_components.py` 9 passed, 0 Chromes left after.
- `test_shell_components.ShellPage` closes its browser when the page never comes up.

## Not done

- No watchdog for a hung window process: a blank window stays blank until the desktop restarts.
- The ~20 short connections a second between kdesk's modules (TIME_WAIT pile-up) are not looked at.
- `hidden_evidence.Browser` (Edge, evidence runs) does not use the job yet.
- Old `state\edge-kdesk-*` profile folders left on disk, not deleted.

## Rough spots

- `kd_window.py` `_page_visible`. Missing world word: none; this is host plumbing (a window shown without its
  toolkit knowing). The deeper gap is that the tucked path bypasses pywebview at all.

- `widget_browser.py` job object. Missing world word: a process the desktop starts belonging to its starter, so
  that ending one ends what it started (the house's `off` covers windows, not helper processes).
