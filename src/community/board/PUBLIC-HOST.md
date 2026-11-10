**STATUS (5 Nov, ~18:50 PT, ran from Alex's PC):** `/` is the website (static, `/srv/seabright/website`). `/meeting` → 302
to the guest invite `/join/<code>` (one line in `/srv/seabright/meeting.conf`). Guest → name → `/board` paints. Signed
out, `/board` paints Announcements, Calendar and Map, and a chat says "Sign in to read the chats". Guest chat send, reply,
react, edit and delete all work at 390×844. The Map paints for guests and visitors. Redeploy:
`bash src/community/deploy/deploy.sh` (deploy/README.md).

Earlier: `/meeting` first answered at ~18:12 PT with the holding page.

# Serving the Seabright board to a plain browser (public host)

Builder notes, Claude, 5 Nov 2026, written while deploying. Labels: **ran**, **read**, **imagined**.

## The box (read/ran)

- Public 443 is not nginx's http server: `/etc/nginx/stream-sni-proxy.conf` is a `stream` block that reads SNI and
  forwards ordinary web names to `127.0.0.1:8444` (ssl). So the Seabright https block listens on `127.0.0.1:8444` /
  `[::1]:8444`, like example.org's. Port 80 has its own Seabright block (ACME webroot `/srv/seabright/acme`, else 301).
- DNS is not proxied by Cloudflare (A record → 203.0.113.10, the box itself; nginx answers directly). Nothing to change at
  Cloudflare. Cert: `/etc/letsencrypt/live/seabright.example.org/` (webroot, auto-renew by certbot's timer).
- **Consequence:** behind the stream proxy every request reaches nginx from 127.0.0.1 (no PROXY protocol), so the entry
  service's per-IP rate limits see one address for the whole town. Turning on `proxy_protocol` would change the listen
  line example.org's block shares, so it was not done tonight.

## Paths the board page needs (read: widget.html, widget-host.js, kd.js, menu.js, theme-live.js, widget-slots.js, door.py)

How it is opened: `GET /board` (kernel, `public_door.py --board-path /board`) answers with a 302:
signed-in member → `/desk/widget.html?widget=<id of the widget named seabright-board>`; signed in but not yet joined →
`/welcome`; anyone else → `/signin` (`--public`). After sign-in the entry service sends people to `SITE_HOME=/board`.

Every path the board page itself touches, all to the **kernel** (127.0.0.1:8810):

| Path | Method | What |
|---|---|---|
| `/board` | GET | the redirect above |
| `/desk/widget.html`, `/desk/kd.js`, `/desk/kd.css`, `/desk/menu.js`, `/desk/theme-live.js`, `/desk/widget-host.js`, `/desk/widget-slots.js` | GET | the trusted parent page and its scripts (only these; anything else under `/desk/` is 404) |
| `/desk/theme.css`, `/desk/theme.json`, `/desk/theme-native.json`, `/desk/theme-wallpaper` | GET | the reader's theme |
| `/desk/widget/<action>` | POST | the widget broker (open, poll, close, stall, and every op: see, do, project, upload, file-check …) |
| `/do`, `/see` | POST | kd.js/menu.js lines (failure reports, menus) |
| `/door/stream` | GET (SSE) | happenings; needs `proxy_buffering off` and a long read timeout |
| `/files/<thing>?variant=content\|thumbnail` | GET | attachments, fetched by the trusted parent |

Simplest safe rule for nginx: `/board`, `/desk/`, `/do`, `/see`, `/door/`, `/files/`, `/upload` → kernel. Also kernel
but not needed by the board page: `/api/*`, `/lens.html` and desk-shell painter files, `/web*`, `/stream`, `/health`,
`/theme.css` (root). None of these collide with `/`, `/assets/*`, `/images/*`, `/_next/*` **unless** the website
uses `/do`, `/see`, `/files`, `/desk`, `/door` or `/board` itself. `/meeting` stays nginx's.

## How the board reaches a plain browser (read/imagined, not yet ran end to end)

- On the desktop the board is a component-painter **widget**: `widget.html` (trusted parent) runs the widget's code in a
  sandboxed srcdoc frame, and the parent talks to the broker (`widgets.py`) at `/desk/widget/*`. The desktop guards the
  broker with `X-Agora-Widget-Host`, a key only its WebView2 windows send (kdesk.py ~426).
- `src/community/deploy/public_door.py` is the kernel door plus that same parent page and broker, unchanged,
  without the header. What still holds the line: the frame is sandboxed with an opaque origin and `connect-src 'none'`;
  a request from it carries `Origin: null`, which the broker refuses; every act runs as the viewer narrowed to the
  widget's grants (Principal), as on the desktop. **What is weaker than the desktop:** WebView2's native guard also stops
  a frame navigating itself away (a way to leak what it read); a browser does not. Fine for reviewed components a
  steward installed; not for unreviewed widget code. (Missing word: a "web host" profile of the widget guard.)
- The broker holds `window.surface` for each open page. On the desktop the window module offers that hold word; here
  `deploy/web_surface.py` (a module in the genesis) offers `window.surface`/`window.bar` and draws nothing.
- The kernel's own `_cross_site` compares Origin with `http://<Host>` only, so behind https every POST would be refused.
  public_door accepts the configured `--origin` too. (Fix belongs in kernel/door.py: compare with the public origin.)
- Grants the board needs, all installed by the existing installers: board GRANTS (ui_install.py) plus, from
  board_activate, `files.*` limited to the library, `hear:attach hear:files.* hear:file-result`, and the map reads
  `map.layers map.tile map.find map.where map.place` (map module fetches tiles from OpenFreeMap from the box).
  `model.ask` / `model.status` are granted but no model module runs on the box: catch-up "summarise" will refuse.

## What was done to the world (ran; all steward lines, no source)

- Founded from `/srv/seabright/genesis.json`: steward = Alex's entry account (made by `deploy/bootstrap_steward.py`),
  modules web-surface, board and files. The installers ran through `deploy/install_board.py`: world, gallery, ui, map,
  asks, documents, activate.
- `visitors on` (r380). `seen-by … everyone` on the Announcements and Meetings & events groups, and on every lens,
  component, part-style, style, widget, button, kind, board-channel, board-order, board-settings, map and map-layer.
  A thing added later needs the same: rerun `steward_setup.py`.
- The board's see-words may=anyone (r513–r520): board.badges/feed/events/catch-up/queue/search/asks, forgotten.
  Leak check (ran): a guest's line in #Bugs was not visible to a visitor through chat, look, feed, catch-up, search,
  badges or rows person. Not checked: an announcement's author name (there was no announcement yet).
- One real guest account, "Test (Claude)", made by the phone checks; its test lines are deleted. A leader can switch it
  off.

## Source changes made tonight

- `src/agora/modules/map/map.py` `the_map`: when the place has the same name as its map ("Seabright"), `look`
  refuses as ambiguous and the map said "Seabright is not a map". It now falls back to `rows map name=`. Source: fix
  (a bug in a general mechanism). Missing-word: none.
- `src/community/deploy/*` (new): public_door.py (host seam), web_surface.py (module seam), the scripts.

## Still missing / known rough

- Module `run` paths in the genesis were resolved through the venv symlink to `/usr/bin/python3.11` (start_kernel's
  `load_genesis` resolves symlinks), and `set` cannot change a module's run. Bridge: `PYTHONPATH` of the venv in
  `seabright-kernel.service`. Missing word: changing a module's run (or load_genesis not resolving symlinks).
- The kernel's `_cross_site` compares only with `http://<Host>`. public_door overrides it; the fix belongs in door.py.
- The guard: the browser host lacks WebView2's no-self-navigation guard (above). Missing word: a web-host widget guard
  profile.
- Every visitor is 127.0.0.1 to nginx (stream SNI proxy). Entry runs with `SITE_IP_LIMITS=off`.
- No model module on the box: catch-up "summarise" refuses.
- Map on a phone: the layers card covers about half the map when it opens.
- Adding steward lines takes about 20 s of board downtime (steward_session.sh), because the public kernel has no
  steward session on the box. Alex's own sign-in (`/srv/seabright/signin-link.sh`) would let him do it live.
- The Let's Encrypt registration used Alex's address (`-m`) for expiry notices.
