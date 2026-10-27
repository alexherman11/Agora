Builder note for Claude, 26 Oct 2026. No live rollout or git mutation.

Missing world-level capability: **a window-owned native identity and geometry lease**.

One shared source file edited: `../kernel-desktop/kd_window.py`.

- Bind private SetPropW/GetPropW signatures.
- When its native window is known, publish `Agora.Window.<thing>` = 1, a Windows
  property removed automatically when that HWND is destroyed. The WM can expose
  `wm.windows.agora` and admit Agora's frameless windows without reading titles.
  This is an identity hint, never an authority or a kernel-write credential.
- In `watch_drags`, skip windows carrying `Agora.WM.Lease` and clear their pending
  hand-drag observation. The existing host otherwise mistakes WM placements for
  hand drags and copies geometry into world facts. The WM owns only live geometry;
  the host continues to own lifecycle and world intent.

No edits to kdesk.py, theme, shell, board or the kernel. The coordinator must
include this small shared seam at rollout; the running host has not loaded it.
This file is also the Board handoff: no live Board writes were made under the
commission's no-live-steps constraint.
