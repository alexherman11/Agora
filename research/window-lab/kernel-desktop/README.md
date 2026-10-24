> Written by Claude (PROOF a13428, epic a13308), 23 October 2026. Claims are labelled **ran** (executed here, numbers as printed), **read** (from source, with what I read) or **imagined**. Alex's words are in quotation marks.

# Your desktop, on the new kernel

Alex, before leaving on 23 Oct: "When i get back i hope that some agora native windows are running in my windows desktop, and they use the new code." This folder is that: real windows on the Windows desktop, drawn from the new kernel (`research/kernel-lab`), not from frontier.

## What is on the screen

- **The Agora taskbar**, a thin strip along the bottom, just above the Windows taskbar. Left: *Agora* (opens Lines), then the buttons and pinned things that are on it (world things with `bar=taskbar`), then the Agora windows that are open (click: bring forward, or tuck away). Right: who holds a surface (*guy · window.overlay*), a clock, and ⏻ (click twice: `off window`). The strip is reserved through the shell (an AppBar), so maximized windows stop above it; it hides while a program is full screen.
- **The Feed**, an app window: the place's feed as a **lens painted by lens.js itself, unchanged**, through the kernel's own painter routes. ♥ likes (sealed), *pin* pins (leaders), *to taskbar* puts the post on the taskbar.
- **The little guy**, a 16×16 pixel person in the desk's colours who walks along the top of the taskbar, hops onto the tops of windows (Agora windows and other programs', never reading their titles), and says things in a bubble. He never takes a click or the focus, and hides while a program is full screen.
- On demand: **Lines** (type any line to the kernel, see receipts and what happens), **Help** (every word you may use, with its help), **Thing** (one thing and its facts).

![The desktop: the Feed lens, the taskbar with a pinned post, the guy](evidence/desktop-lens-feed-and-taskbar.jpg)

## On and off

| To | Say (a word, in Lines or from an agent) | Or click |
|---|---|---|
| Stop the guy | `stop guy` (a verb note for `off guy`) | |
| Stop every Agora window and the strip | `stop window` | ⏻ on the taskbar, twice |
| Turn either back on | `undo` | |
| Stop everything, now, and give the screen back | | Start → Agora → **Agora desktop off** (`kdesk_off.py`) |
| Start it all | | Start → Agora → **Agora desktop on** (`kdesk_on.py`) |

The words are switches inside the world (recorded, undoable). The two scripts stop and start processes and write nothing to the world, so the next start shows exactly what the world says. The off script ends the kernel's process tree and its modules, and checks the screen's work area is whole again. It does not touch the home base (`hud.py`, Ctrl+Alt+J), the frontier keeper, or the Windows taskbar.

## How it is made

```
 kdesk.py (one process, started detached under pythonw: no console)
   the kernel, research/kernel-lab/kernel, UNCHANGED, with nothing added (kext.py is gone since 12a4a82)
   its door on 127.0.0.1:8810: /do /see /door/stream, the painter's routes (/api/scene ...), /dev/signin, + /desk/<page>
   a stand-in for sign-in, in process: Alex's session (his pages) and "agent for Alex" (label claude), in keep/
   modules, started by the kernel as the world says (SHAPE 11, newline JSON on stdin/stdout):
     window  kd_window.py   publishes window.list (see), window.open/move/close/focus (do), window.opened (hear),
                            window.overlay (hold). It makes the screen match the world's `window` things.
     guy     kd_guy.py      publishes guy.say, guy.hop, guy.sit (do); holds window.overlay; sees window.list all.
```

**Windows are world things; the screen follows the world.** `window.open feed` is a line; the window module answers it with a line, `make kind=window shows=feed lens=feed at=.. size=..`, which the kernel admits as one record "by window for Alex". The module then opens a WebView2 window to match, level-triggered (after every happening it hears, and every few seconds). So undo of a `window.open` closes it, undo of a `window.close` reopens it where it was, a rule can open or move windows, and after `stop window` and `undo` (or a restart) every window comes back where the world says. When Alex drags or resizes a window, the module records where he left it (`set <window> at=.. size=..`, by the module, on its own grants). Closing a window by its × is the line `window.close`.

**Changed by words alone.** Everything on the taskbar is world data. As Alex's agent, I made the taskbar's buttons, the `stop` word, the feed lens and the guy's rule with lines only (**ran**, records r17 to r24 of the live world, by "agent for Alex"):

```
verb stop steps="off $1" help="stop <module>: the same as off (stop guy, stop window). undo turns it on again."
make kind=button bar=taskbar label=Feed does="window.open feed" order=1
make kind=button bar=taskbar label=Help does="window.open help" order=2
make kind=button bar=taskbar label=Wave does="guy.say hi Alex!" order=3
make kind=rule on=window.opened do="guy.hop $target"
make kind=lens name=feed text="<lenses/feed.lens>"
```

A button's `does` runs as whoever presses it. A pinned thing (`make kind=pin bar=taskbar shows=<thing>`, what *to taskbar* in the feed does) opens that thing. A new verb note composes words: `verb side steps="set $1 at=24,40; set $2 at=1300,40" help="..."`, then a button can `does="side <a> <b>"`. A do verb is one act and one record, so one `undo` puts both windows back; the screen follows because windows are world things. Module words compose too (kernel 12a4a82): `verb shove steps="window.move $1 to=left"` is an alias of `window.move`, and `verb swap steps="window.move $1 to=right; set $2 at=500,40"` is still one act that one undo takes back (**ran**, hidden checks). The kernel asks you to look at a thing before you set it; `window.list` reads the window things inside the call, as the caller, so listing them counts as that look.

**The four kinds of word, all used.** do (`window.open`, `guy.say`), see (`window.list`, `rows`, `holds`), hear (`window.opened`, heard by the guy and by the rule), hold (`window.overlay`: the guy asks the kernel for it on his own grants and gets a lease; `holds` lists it; `off guy` ends it).

**Powers.** The window module's grant is narrowed to window things (`only=kind:window`): on its own it may make windows and nothing else (**ran**: `make kind=button ...` refused, "window's grant for make reaches only window things, not a button"). It opens windows only for the desktop's owner and their agents (**ran**: a second person's `window.open lines` refused). The guy holds only his words, `window.list`, `rows`, `look`, `window.overlay` and `hear:window.opened`.

**The painter.** App windows are lens.js. A lens window is a frameless WebView2 window holding a thin frame page (its strip to drag and close by) and lens.js in it, unchanged, asking the kernel's `/api/scene` with Alex's session cookie, set HttpOnly by `/dev/signin` when the window host opened it. The taskbar, Lines, Help and Thing pages are the host's own chrome, drawn by `pages/kd.js` from rows, because the lens language has no words yet for a ticking clock or which window is in front.

## Files

| File | What it is |
|---|---|
| `kdesk.py` | the process: kernel + extension, the door with `/desk/`, the sign-in stand-in, the genesis of Alex's desktop world |
| `kd_window.py` | the window module and the desktop host: WebView2 windows, the AppBar strip, drags, closes, full-screen step-back |
| `kd_guy.py`, `sprite.py` | the little guy: his module, his walking and hopping, his picture in a layered (per-pixel alpha) window |
| `modproto.py` | the module protocol for a Python module |
| `pages/` | the taskbar, the frame around a lens, Lines, Help, Thing |
| `lenses/feed.lens` | the feed lens, as made in the world (the world's copy is the truth) |
| `kdesk_on.py`, `kdesk_off.py` | start detached (WMI, outside any session's job, under pythonw); stop everything and check the screen |
| `kd_say.py` | say lines as Alex's agent (or `--as alex`) |
| `press.py` | a real mouse click or drag, for demos |
| `test_kdesk.py` | 12 hidden checks: fresh worlds, real HTTP, the modules as real processes in `--headless` mode |
| `state/` (ignored) | the live world (`state/world`, log and keep), `kdesk.log`, the modules' logs in `state/world/modules/<name>/stderr.log` |

## Evidence

**Ran**, 23 Oct 2026, Windows 11, one 3840×2160 monitor at 150%, Python 3.12 (the pinned venv), the kernel at commit 529f1b1 plus its working tree of 18:54:
- The hidden checks: `Ran 12 tests in 22.160s`, `OK`; after the last changes, `Ran 12 tests in 18.936s`, `OK`; on the kernel at 2d872eb with kext slimmed to the log file, `Ran 12 tests in 20.483s`, `OK`; on 12a4a82 with kext gone, `Ran 12 tests in 22.951s`, `OK`. After that change the live world (founded on the older kernel) opened on a copy, hidden, its rule fired once per `window.opened` (it had fired twice while kext's rules and the kernel's both ran), and the live desktop was restarted on it: strip, Feed and the guy back where they were. They cover: the taskbar made by the window module on its own; open, move, close and undo of a window; `off window` and undo; a button made by a line and pressed; a verb note composing window words; a rule hearing `window.opened`; `stop` as a verb note, ending the guy's hold, and undo bringing it back; `look guy`, `holds`, `guy.say`, `status guy`; the window grant's narrowing; owner-only windows; the stream carrying a happening; a lens window opened through `/dev/signin` and painting a post through `/api/scene`; replay giving the same world.
- On the real desktop, by real clicks (`press.py`) and lines: the taskbar's Side by side button moved Feed (trial world, r27); a drag of Feed by its strip was recorded as `set dk32 at=2241,409 size=1180,1500 [r31]`; Help's taskbar chip brought it forward, its × closed it (`window.close dk38`, r34), and `undo` reopened it (r35, "put back 8 facts"); in the live world, *to taskbar* in the Feed lens made `make kind=pin bar=taskbar shows=dk37` (r30) and the taskbar showed it; ♥ made a sealed like (r31, `by: sealed`) and the lens showed ♥ 1; Wave made the guy say "hi Alex!".
- The strip: the shell's work area went from 2088 to 2022 with it and back to 2088 when it stopped, every time (after `off window`, after `kdesk_off.py`, and after a hard kill of a probe, 625 ms).
- Full screen: with a full-screen window in front, the strip and the guy were both hidden, and both came back after it closed.
- The Start-menu shortcuts: *off* left the work area at 2088 and 8810 quiet; *on* brought the strip back and the kernel answering with 32 records, the Feed window where it had been.

**Read**: the kernel's code at 18:54 (kernel.py, words.py, modules.py, door.py, painter.py) for every place this folder stands on it.

**Not verified**: a real game in full screen (the test used a full-screen window); a second monitor; what happens to the strip when the home base is shown over it (it should hide, since the home base covers the monitor: **imagined**); a restart of Windows (nothing starts it at logon; see below).

## What I found (rough spots, for the kernel and the next builder)

- pywebview's colour-key transparency failed after a window moved (a grey box around the guy, twice), so the guy is a layered window with per-pixel alpha, drawn by PIL, with no browser engine.
- Setting `argtypes` on the shared `ctypes.windll.user32` breaks pywebview's own calls (its drag failed with a TypeError). Use a private `ctypes.WinDLL("user32")`.
- pywebview enforces a 100-point minimum window height, so a 66-pixel strip came out 150 pixels tall and covered the Windows taskbar until `min_size` was set.
- The shell's full-screen notice (ABN_FULLSCREENAPP) did not reach the strip in the test; the window module checks the foreground window itself.
- A start through `cmd /c` from WMI showed a black console on Alex's screen (19:04, for a minute); it now starts under pythonw.
- The kernel keeps dictionary entries out of `make` and `set`, so a verb note needs its own word (`verb`), and a world-made alias needs one too (none yet; `stop` is a verb note instead).
- A module does not hear its own acts, so after answering with lines the window module looks again by itself.
- `ModuleProcess._read` handled a fixed set of messages; adding `do`/`see` on a module's own meant copying it. The kernel now has `handle(msg)`.
- A do verb could not compose module words (2d872eb kept a verb to kernel words). Raised with the kernel builder, who changed it the same evening (12a4a82): a one-step module verb is an alias, and a longer one joins the module's answer lines into the verb's one record. The design's example, a room making `play` mean `media.play`, can be written now.
- kext.py (what this folder once added to the kernel: `rows`, verb notes, rules, a module acting on its own, narrowed grants, a fuller hello, module log files) was taken into the kernel item by item on 23 Oct and deleted; module logs are in `<world>/modules/<name>/stderr.log`.

## What is not done

- Nothing starts the desktop when Windows starts. Adding it to the Startup folder (as Agora.lnk does for the home base) is one line, left for Alex or the coordinator to decide.
- The taskbar is not a lens yet: it needs a clock and "which window is in front" as rows the painter can read. Posting from the Feed lens needs the composer, which the facade does not carry; posting is a line in Lines.
- Window things are visible to the whole place (the kernel reserves `sees` for itself). On a desktop of one person that is only Alex; in a shared world windows should be the person's view (SHAPE 2).
