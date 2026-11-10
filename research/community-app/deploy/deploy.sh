#!/usr/bin/env bash
# Push the Seabright code to the box and restart its two services. Run from git-bash anywhere:
#     bash research/community-app/deploy/deploy.sh            # code + restart kernel and entry
#     bash research/community-app/deploy/deploy.sh --no-restart
# Sends only the code the services run (no worlds, no var/, no .env, no pickles, no evidence). The world
# (/srv/seabright/world), the entry data (/srv/seabright/entry-data) and the settings (/etc/seabright/env) stay put.
# Claude, 5 Nov 2026. See README.md beside this file.
set -euo pipefail
BOX="${SEABRIGHT_BOX:-root@100.101.155.17}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

NOTATION_PY=$(cd research/text-desk-lab/notation && ls *.py | grep -v '^test_' | sed 's#^#research/text-desk-lab/notation/#')

echo "packing from $ROOT"
tar -cz \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='evidence' --exclude='*.pickle' \
  --exclude='var' --exclude='.env' --exclude='.env.*' --exclude='*.sqlite3*' --exclude='node_modules' \
  --exclude='state' --exclude='house-state' --exclude='sessions' \
  research/kernel-lab \
  research/community-app \
  research/window-lab/kernel-desktop/widgets.py \
  research/window-lab/kernel-desktop/pages \
  research/text-desk-lab/notation/desk-shell \
  research/text-desk-lab/notation/sources \
  $NOTATION_PY \
  | ssh "$BOX" 'set -e; exec 9>/srv/seabright/deploy.lock; flock 9;   # two deploys at once wait, never collide
      rm -rf /srv/seabright/app.new; mkdir -p /srv/seabright/app.new;
      tar -xz -C /srv/seabright/app.new;
      if [ -d /srv/seabright/app ]; then rm -rf /srv/seabright/app.old; mv /srv/seabright/app /srv/seabright/app.old; fi;
      mv /srv/seabright/app.new /srv/seabright/app; du -sh /srv/seabright/app'

if [ "${1:-}" != "--no-restart" ]; then
  ssh "$BOX" 'systemctl restart seabright-entry seabright-kernel; sleep 3;
      systemctl is-active seabright-entry seabright-kernel;
      curl -s -o /dev/null -w "kernel /health %{http_code}\n" http://127.0.0.1:8810/health;
      curl -s -o /dev/null -w "entry /healthz %{http_code}\n" http://127.0.0.1:8817/healthz'
fi
