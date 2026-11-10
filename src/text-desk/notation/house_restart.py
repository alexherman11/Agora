"""house_restart.py (a10269): a restart of the house asked for from the world, with its reason on record.

Rough spot a9135: a restart only ever happened as a side effect of landing a house file. Alex allows one whenever
nothing important would break (charter, 21 Oct). Now the world verb `restart-house <why>` (restart-house.verb beside
this file; a note tagged verb, on=house) makes a note role=house-restart state=asked why=... asked_by=<you> in your
corner, and the house:

  - takes it only from those the house note's restart_by= names (default jeff,alex), and only with a reason;
    otherwise state=refused, saying why;
  - refuses game evidence or unknown/unsafe screen state (the house's own observation, never a caller's),
    at the request and again at the moment of restarting; fullscreen geometry or an unlisted app alone
    is not evidence of a game. Native/browser admission retains its separate, stricter policy;
  - drains: no new turn starts (the same drain a landing's restart uses), and the note says what is still in flight
    (in_flight=), until nothing is: a turn is never cut for a requested restart (a landing's restart still cuts
    after RESTART_GRACE, as before);
  - exits 75, as a landing's restart does, so the keeper starts it again at once; residents and workers resume their
    own sessions, drafts and receipts as at any restart;
  - the new house finds the note at state=restarting, says state=done with its new pid and start time, and comments
    to the asker. A note restarts the house once: a note already restarting or done is never taken again, and
    several notes asked together ride one restart.

The asker may set state=cancelled while it drains; the drain ends if nothing else asked for it. Without the keeper
(no HOUSE_KEEPER) nothing restarts and the note says so.
"""
import os
import time

import persons

ROLE = "house-restart"
DEFAULT_BY = "jeff,alex"


def requests(w):
    """[(appearance id, subject)] of every restart note that shows somewhere."""
    out = []
    for sid, s in w.subjects.items():
        if (s.get("props") or {}).get("role") == ROLE:
            apps = w.appearances_of(sid)
            if apps:
                out.append((apps[0], s))
    return sorted(out, key=lambda x: x[0])


def maker(w, sid):
    """Who made the note (its create event's author), never a prop anyone can write."""
    for e in w.events:
        if (e.get("undo") or {}).get("delete_subject") == sid and not e.get("undone"):
            return str(e.get("by") or "").split("/")[0].lower()
    return ""


def game_seen(nongame=""):
    """The house's own guard reading: a reason the restart must not happen now, or "" when none.
    Restart-only policy: geometry/app naming does not establish a game.
    Retain Windows' game indication and unknown/unsafe observation refusal.
    This does not change guard_context.policy_clear or native-run admission."""
    import guard_context
    try:
        data = guard_context.observe(nongame)
    except Exception as exc:
        return f"the guard could not be read ({type(exc).__name__}); not restarting blind"
    if not isinstance(data, dict):
        return "the guard observation is malformed; not restarting blind"
    if data.get("game") is True or data.get("notification_state") == 3:
        return "the guard sees a game (full-screen Direct3D)"
    if (type(data.get("notification_result")) is not int or data["notification_result"] != 0
            or data.get("foreground_known") is not True
            or data.get("input_desktop") != "Default"):
        return "the guard cannot establish a stable foreground on the unlocked desktop; not restarting blind"
    exe = data.get("foreground_exe")
    if (not isinstance(exe, str) or not exe or exe.lower() == "unknown"
            or "/" in exe or "\\" in exe):
        # observe marks transitions during its probes unknown, too.
        return "the guard foreground identity is unknown or changed; not restarting blind"
    state = data.get("notification_state")
    if type(state) is not int or state not in (2, 5):
        return "the guard reports an unavailable, busy or presentation state; not restarting now"
    if ("game" not in data or
            (data["game"] is not False and not (state == 2 and data["game"] is None))):
        return "the guard game reading is unknown or inconsistent; not restarting blind"
    return ""


def should_exit(owns, busy, waited, grace):
    """The run loop's question. A requested restart (owns) waits for idle and never cuts a turn; a landing's restart
    waits for idle or `grace` seconds, as it always has."""
    if not busy:
        return True
    return not owns and waited >= grace


class Restarts:
    def __init__(self, house, game=None, clock=time.time, pid=None):
        self.house, self.game, self.clock = house, game, clock
        self.pid, self.started = pid or os.getpid(), clock()
        self.pending = set()        # note ids this house is draining for
        self.owns = False           # this drain was begun by a request, not by a landing
        self.flight = None

    # -- the house's lines -------------------------------------------------------------------------------------------
    def _set(self, aid, **props):
        tail = " ".join(f'{k}="{str(v)}"' for k, v in props.items())
        self.house.act("house", f"look {aid} :1; do prop {aid} {tail}")

    def _tell(self, aid, words):
        self.house.act("house", f"look {aid} :1; do comment {aid} line=\"{words}\"")

    def _guard(self, cfg):
        game = self.game if self.game is not None else game_seen
        return game(cfg.get("guard_nongame", ""))

    # -- at start: the restart that brought this house up ------------------------------------------------------------
    def started_up(self, w):
        at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.started))
        for aid, s in requests(w):
            p = s.get("props") or {}
            if p.get("state") == "restarting" and str(p.get("old_pid", "")) != str(self.pid):
                self._set(aid, state="done", new_pid=self.pid, started=at, in_flight="none")
                self._tell(aid, f"The house restarted: new pid {self.pid}, started {at} (was {p.get('old_pid', '?')}).")

    # -- each pass ---------------------------------------------------------------------------------------------------
    def step(self, w, cfg, busy, keeper=True):
        ws = self.house.workshop
        allowed = cfg.get("restart_by") or DEFAULT_BY
        for aid, s in requests(w):
            p = s.get("props") or {}
            state = p.get("state", "")
            if state == "cancelled" and aid in self.pending:
                self.pending.discard(aid)
                continue
            if state != "asked":
                continue
            who = maker(w, s["id"])
            why = str(p.get("why", "")).strip().strip('"')
            why = why[4:].strip() if why.lower().startswith("why=") else why
            if not who or not persons.holds(w, allowed, who):
                self._set(aid, state="refused", refused=f"only {allowed} may ask the house to restart (restart_by on the house note)")
                continue
            if not why:
                self._set(aid, state="refused", refused="a restart needs a reason: restart-house <why>")
                continue
            if not keeper:
                self._set(aid, state="refused", refused="this house runs without the keeper (HOUSE_KEEPER), so nothing would start it again")
                continue
            seen = self._guard(cfg)
            if seen:
                self._set(aid, state="refused", refused=seen)
                self._tell(aid, f"Not restarting: {seen}. Ask again when it is clear.")
                continue
            self._set(aid, state="waiting", asked_by_checked=who, accepted=time.strftime("%H:%M:%S", time.localtime(self.clock())))
            self.pending.add(aid)
        if self.pending and not ws.restart_wanted:
            ws.restart_wanted, self.owns = True, True
        if not self.pending and self.owns:
            ws.restart_wanted, self.owns = False, False     # cancelled: a landing's own restart is found again by the HEAD watch
        if self.pending:
            flight = ", ".join(busy) or "nothing"
            if flight != self.flight:
                self.flight = flight
                for aid in sorted(self.pending):
                    self._set(aid, in_flight=flight)

    def leaving(self, cfg):
        """Just before the exit. -> False to stay (a game began while it drained: every pending note is refused)."""
        if self.owns:
            seen = self._guard(cfg)
            if seen:
                for aid in sorted(self.pending):
                    self._set(aid, state="refused", refused=seen, in_flight="none")
                    self._tell(aid, f"Not restarting after all: {seen}. Ask again when it is clear.")
                self.pending.clear()
                self.house.workshop.restart_wanted, self.owns = False, False
                return False
        for aid in sorted(self.pending):
            self._set(aid, state="restarting", old_pid=self.pid, in_flight="none")
        self.pending.clear()
        return True
