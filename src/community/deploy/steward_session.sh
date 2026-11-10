#!/bin/sh
# On the box, as root: stop the public kernel, open the same world on loopback with a one-off steward dev session, run a
# steward script against it, then remove the session and start the public kernel again (about 20 s of board downtime).
#     sh /srv/seabright/app/src/community/deploy/steward_session.sh <script.py> [args...]
# The script gets --door http://127.0.0.1:8890 --token-file <file>. Claude, 5 Nov 2026.
set -e
APP=/srv/seabright/app
W=/srv/seabright/world
STEWARD=$(/srv/seabright/venv/bin/python -c "import json;print(json.load(open('/srv/seabright/genesis.json'))['steward']['account'])")
TOKF=/srv/seabright/.steward-token
cleanup() {
  pkill -u seabright -f "start_kernel.py --world $W" 2>/dev/null || true
  rm -f "$W/keep/dev-sessions.json" "$TOKF"
  systemctl start seabright-kernel
}
trap cleanup EXIT
systemctl stop seabright-kernel
TOK=$(openssl rand -hex 24)
umask 077
printf '{"%s": {"account": "%s"}}' "$TOK" "$STEWARD" > "$W/keep/dev-sessions.json"
printf '%s' "$TOK" > "$TOKF"
chown seabright:seabright "$W/keep/dev-sessions.json" "$TOKF"
cd $APP
sudo -u seabright /srv/seabright/venv/bin/python src/agora/start_kernel.py --world $W --port 8890 --dev-entry 8891 > /srv/seabright/steward-kernel.log 2>&1 &
for i in $(seq 1 30); do curl -sf http://127.0.0.1:8890/health >/dev/null && break; sleep 1; done
SCRIPT=$1; shift
sudo -u seabright /srv/seabright/venv/bin/python "$SCRIPT" --door http://127.0.0.1:8890 --token-file "$TOKF" "$@"
