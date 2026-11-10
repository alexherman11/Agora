# Seabright public host: deploy

Builder notes, Claude, 5 Nov 2026. The site at https://seabright.example.org runs on Alex's Hetzner box (Debian 12),
which is reached only over Tailscale: `ssh root@100.101.155.17`. How the board reaches a plain browser, which paths go
where, and what is still missing: [PUBLIC-HOST.md](../board/PUBLIC-HOST.md).

## Redeploy (one command, from git-bash)

```bash
bash research/community-app/deploy/deploy.sh               # push code, restart both services, print health
bash research/community-app/deploy/deploy.sh --no-restart
```

It tars only `research/kernel-lab`, `research/community-app`, the desktop's `widgets.py` and `pages/`, and the
desk-shell painter files with `text-desk-lab/notation/*.py` (the lens painter imports them). It leaves out evidence,
`var/`, `.env*`, pickles, sqlite files, `state/`, `sessions/` and `house-state/`. The upload goes to
`/srv/seabright/app.new` and is then swapped into `/srv/seabright/app`; the previous copy stays as `app.old`.
Deploying changes **code only**. A new board lens or bundle reaches the world only through its installer (below).

## On the box

| What | Where |
|---|---|
| kernel door (public_door.py) | `seabright-kernel.service`, 127.0.0.1:8810, world `/srv/seabright/world` |
| entry service | `seabright-entry.service`, 127.0.0.1:8817, data `/srv/seabright/entry-data` |
| settings (secret inside, root 600) | `/etc/seabright/env` |
| genesis used to found the world | `/srv/seabright/genesis.json` (steward = Alex's entry account) |
| nginx (this name only) | `/etc/nginx/sites-available/seabright` = `nginx-seabright.conf` here |
| `/meeting` target (one line) | `/srv/seabright/meeting.conf`, then `nginx -t && systemctl reload nginx` |
| website (static) | `/srv/seabright/website` |
| holding page | `/srv/seabright/holding/index.html` |
| Alex's one-time sign-in link | `/srv/seabright/signin-link.sh [email]` (root; works once, for 15 min) |
| venv | `/srv/seabright/venv` (loro, Pillow, pypdf) |

Both services run as the `seabright` system user, with `Restart=always`, listening on loopback only.

## Steward lines on the live world

`steward_session.sh <script> [args]` stops the public kernel, opens the same world on loopback with a one-off steward
dev session, runs the script, then deletes the session and starts the kernel again (about 20 s of board downtime):

```bash
D=/srv/seabright/app/research/community-app/deploy
sh $D/steward_session.sh $D/install_board.py --only ui                # new board.lens / bundles into the world
sh $D/steward_session.sh $D/steward_setup.py --python /srv/seabright/bin/python   # visitors on + seen-by everyone
sh $D/steward_session.sh $D/visitor_words.py                          # board see-words may=anyone
sh $D/steward_session.sh $D/steward_lines.py --line "see:rows module"  # any lines
```

## Checks (hidden headless Edge on this PC, nothing on screen)

- `phone_check.py`: website, signed-out board, `/meeting` → guest name → board (it makes a real guest).
- `mobile_check.py --cookies <scratch file>|none --steps "Announcements,Calendar,# Bugs,Map" [--js ...]`: presses
  nav items inside the painter's frame and takes screenshots into `evidence/`.
