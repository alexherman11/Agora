"""Who you are: accounts, invites, sign-in requests and sessions.

No HTTP here, so the rules can be read and tested on their own. Secrets that
travel (session cookies, sign-in links, codes) are stored only as hashes.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from dataclasses import dataclass

from .config import Config
from .db import Store
from .questions import Questions

EMAIL_RE = re.compile(r"^[^@\s<>\"',;]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                      r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
CODE_ATTEMPTS = 5
FLOW_SECONDS = 600
INVITE_EXPIRY_DAYS = (1, 7, 30, 90, 365)
CHANNEL_MAX = 60


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_email(raw: str) -> str | None:
    email = (raw or "").strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        return None
    return email


def new_id(prefix: str) -> str:
    alphabet = "abcdefghijkmnpqrstuvwxyz23456789"
    return prefix + "".join(secrets.choice(alphabet) for _ in range(20))


def new_invite_code() -> str:
    # 12 characters of an unambiguous alphabet: about 62 bits, easy to read off a poster.
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(12))


@dataclass
class InviteState:
    invite: dict | None
    status: str  # "open", "missing", "frozen", "expired", "full"

    @property
    def open(self) -> bool:
        return self.status == "open"


class SignInRefused(Exception):
    """A sign-in that cannot go ahead. `reason` is shown to the person."""

    def __init__(self, reason: str, kind: str = "refused"):
        super().__init__(reason)
        self.reason, self.kind = reason, kind


class Service:
    def __init__(self, cfg: Config, store: Store, questions: Questions, clock=time.time):
        self.cfg, self.store, self.questions, self.clock = cfg, store, questions, clock

    def now(self) -> int:
        return int(self.clock())

    def _mac(self, purpose: str, value: str) -> str:
        return hmac.new(self.cfg.secret_key, f"{purpose}:{value}".encode(), "sha256").hexdigest()

    # -- accounts ---------------------------------------------------------
    def account(self, account_id: str) -> dict | None:
        row = self.store.one("SELECT * FROM accounts WHERE id=?", (account_id,))
        return dict(row) if row else None

    def account_by_email(self, email: str) -> dict | None:
        row = self.store.one("SELECT * FROM accounts WHERE email=?", (email,))
        return dict(row) if row else None

    def answers(self, account_id: str) -> dict:
        rows = self.store.all("SELECT key, value FROM answers WHERE account_id=?", (account_id,))
        return {r["key"]: json.loads(r["value"]) for r in rows}

    def _create_account(self, conn, email: str, invite: dict | None, *, google_sub=None,
                        suggested_name=None, method: str) -> str:
        account_id, now = new_id("acct_"), self.now()
        conn.execute(
            "INSERT INTO accounts(id, email, email_verified, google_sub, suggested_name, invite_id,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (account_id, email, 1, google_sub, suggested_name,
             invite["id"] if invite else None, now, now))
        if invite:
            conn.execute("INSERT INTO invite_uses(invite_id, account_id, at) VALUES (?,?,?)",
                         (invite["id"], account_id, now))
            self.store.event(conn, now, "invite.used", account_id, invite_id=invite["id"],
                             channel=invite["channel"])
        self.store.event(conn, now, "account.created", account_id, method=method,
                         invite_id=invite["id"] if invite else None)
        if email in self.cfg.leaders:
            self._grant(conn, account_id, "leader", "config")
        return account_id

    def _grant(self, conn, account_id: str, role: str, by: str) -> None:
        conn.execute("INSERT OR IGNORE INTO roles(account_id, role, granted_at, granted_by)"
                     " VALUES (?,?,?,?)", (account_id, role, self.now(), by))

    def roles(self, account_id: str) -> set[str]:
        return {r["role"] for r in self.store.all(
            "SELECT role FROM roles WHERE account_id=?", (account_id,))}

    def save_answers(self, account_id: str, values: dict, display_name: str) -> None:
        now = self.now()
        with self.store.connect() as conn:
            for key, value in values.items():
                conn.execute(
                    "INSERT INTO answers(account_id, key, value, questions_version, answered_at)"
                    " VALUES (?,?,?,?,?) ON CONFLICT(account_id, key) DO UPDATE SET"
                    " value=excluded.value, questions_version=excluded.questions_version,"
                    " answered_at=excluded.answered_at",
                    (account_id, key, json.dumps(value), self.questions.version, now))
            first = conn.execute("SELECT onboarded_at FROM accounts WHERE id=?",
                                 (account_id,)).fetchone()["onboarded_at"] is None
            conn.execute("UPDATE accounts SET display_name=?, updated_at=?,"
                         " onboarded_at=COALESCE(onboarded_at, ?) WHERE id=?",
                         (display_name, now, now, account_id))
            self.store.event(conn, now, "account.onboarded" if first else "account.updated",
                             account_id, display_name=display_name,
                             keys=sorted(values), questions_version=self.questions.version)

    # -- invites ----------------------------------------------------------
    def invite_by_code(self, code: str) -> InviteState:
        if not code or len(code) > 40:
            return InviteState(None, "missing")
        row = self.store.one("SELECT * FROM invites WHERE code=?", (code,))
        return self._state(dict(row) if row else None)

    def invite_by_id(self, invite_id: str) -> InviteState:
        row = self.store.one("SELECT * FROM invites WHERE id=?", (invite_id,))
        return self._state(dict(row) if row else None)

    def _state(self, inv: dict | None) -> InviteState:
        if inv is None:
            return InviteState(None, "missing")
        if inv["frozen_at"] is not None:
            return InviteState(inv, "frozen")
        if inv["expires_at"] <= self.now():
            return InviteState(inv, "expired")
        if inv["max_uses"] is not None and inv["uses"] >= inv["max_uses"]:
            return InviteState(inv, "full")
        return InviteState(inv, "open")

    def make_invite(self, maker_id: str, channel: str, kind: str, max_uses: int | None,
                    expires_days: int) -> dict:
        channel = " ".join((channel or "").split())
        if not channel or len(channel) > CHANNEL_MAX:
            raise ValueError(f"Give the channel a name of up to {CHANNEL_MAX} characters.")
        if kind not in ("link", "event"):
            raise ValueError("Unknown invite kind.")
        if max_uses is not None and not 1 <= max_uses <= 10000:
            raise ValueError("Uses must be between 1 and 10,000, or left blank.")
        if expires_days not in INVITE_EXPIRY_DAYS:
            raise ValueError("Pick one of the expiry choices.")
        now = self.now()
        invite = {"id": new_id("inv_"), "code": new_invite_code(), "maker_id": maker_id,
                  "channel": channel, "kind": kind, "max_uses": max_uses, "uses": 0,
                  "expires_at": now + expires_days * 86400, "frozen_at": None,
                  "frozen_by": None, "created_at": now}
        with self.store.connect() as conn:
            conn.execute(
                "INSERT INTO invites(id, code, maker_id, channel, kind, max_uses, uses, expires_at,"
                " created_at) VALUES (?,?,?,?,?,?,0,?,?)",
                (invite["id"], invite["code"], maker_id, channel, kind, max_uses,
                 invite["expires_at"], now))
            self.store.event(conn, now, "invite.made", maker_id, invite_id=invite["id"],
                             channel=channel, kind=kind, max_uses=max_uses,
                             expires_at=invite["expires_at"])
        return invite

    def set_frozen(self, invite_id: str, by: str, frozen: bool) -> bool:
        now = self.now()
        with self.store.connect() as conn:
            if frozen:
                n = conn.execute("UPDATE invites SET frozen_at=?, frozen_by=? WHERE id=?"
                                 " AND frozen_at IS NULL", (now, by, invite_id)).rowcount
            else:
                n = conn.execute("UPDATE invites SET frozen_at=NULL, frozen_by=NULL WHERE id=?"
                                 " AND frozen_at IS NOT NULL", (invite_id,)).rowcount
            if n:
                self.store.event(conn, now, "invite.frozen" if frozen else "invite.unfrozen",
                                 by, invite_id=invite_id)
        return bool(n)

    def _consume_invite(self, conn, invite_id: str) -> dict | None:
        """Count one use if the invite is still open, in the caller's transaction."""
        n = conn.execute(
            "UPDATE invites SET uses=uses+1 WHERE id=? AND frozen_at IS NULL AND expires_at>?"
            " AND (max_uses IS NULL OR uses<max_uses)", (invite_id, self.now())).rowcount
        if n != 1:
            return None
        return dict(conn.execute("SELECT * FROM invites WHERE id=?", (invite_id,)).fetchone())

    def invites(self) -> list[dict]:
        rows = self.store.all(
            "SELECT i.*, a.display_name AS maker_name, a.email AS maker_email FROM invites i"
            " LEFT JOIN accounts a ON a.id=i.maker_id ORDER BY i.created_at DESC")
        out = []
        for r in rows:
            d = dict(r)
            d["status"] = self._state(dict(r)).status
            out.append(d)
        return out

    def invite_people(self, invite_id: str) -> list[dict]:
        return [dict(r) for r in self.store.all(
            "SELECT u.at, a.id, a.display_name, a.email FROM invite_uses u JOIN accounts a"
            " ON a.id=u.account_id WHERE u.invite_id=? ORDER BY u.at", (invite_id,))]

    def public_invite(self) -> InviteState | None:
        row = self.store.one("SELECT value FROM settings WHERE key='public_invite_id'")
        return self.invite_by_id(row["value"]) if row else None

    def set_public_invite(self, invite_id: str | None, by: str) -> None:
        with self.store.connect() as conn:
            if invite_id:
                conn.execute("INSERT INTO settings(key, value) VALUES ('public_invite_id', ?)"
                             " ON CONFLICT(key) DO UPDATE SET value=excluded.value", (invite_id,))
            else:
                conn.execute("DELETE FROM settings WHERE key='public_invite_id'")
            self.store.event(conn, self.now(), "site.public_invite", by, invite_id=invite_id)

    # -- may admit -------------------------------------------------------
    def _admit(self, conn, email: str, invite_id: str | None):
        """For a person without an account: the invite they may come in on.

        Returns (invite or None). Raises SignInRefused when there is no way in.
        """
        if invite_id:
            invite = self._consume_invite(conn, invite_id)
            if invite:
                return invite
            if email not in self.cfg.leaders:
                raise SignInRefused("This invite link has closed. Ask whoever sent it for a new one.",
                                    "invite_closed")
        if email in self.cfg.leaders:
            return None
        raise SignInRefused("You'll need an invite link to join. Ask a neighbour who's already in.",
                            "no_invite")

    # -- email sign-in -------------------------------------------------------
    def request_email_signin(self, email: str, invite_code: str | None) -> tuple[str, dict]:
        """Make a sign-in request. Returns (request id, what to send).

        The page says the same thing whatever happens, so it never tells a
        stranger whether an address has an account. The email says the truth.
        """
        now = self.now()
        account = self.account_by_email(email)
        invite_state = self.invite_by_code(invite_code) if invite_code else None
        may = (account is not None and account["disabled_at"] is None) or \
              (account is None and ((invite_state and invite_state.open) or email in self.cfg.leaders))
        request_id = new_id("req_")
        token = code = None
        if may:
            token = secrets.token_urlsafe(32)
            code = f"{secrets.randbelow(1_000_000):06d}"
        with self.store.connect() as conn:
            conn.execute("UPDATE email_requests SET used_at=? WHERE email=? AND used_at IS NULL",
                         (now, email))
            conn.execute(
                "INSERT INTO email_requests(id, email, token_hash, code_hash, invite_id, created_at,"
                " expires_at) VALUES (?,?,?,?,?,?,?)",
                (request_id, email, sha256(token) if token else None,
                 self._mac("code", f"{request_id}:{code}") if code else None,
                 invite_state.invite["id"] if (may and invite_state and invite_state.open) else None,
                 now, now + self.cfg.link_minutes * 60))
        if not may:
            if account is not None:
                return request_id, {"kind": "none"}
            if invite_state and invite_state.status != "missing":
                return request_id, {"kind": "invite_closed"}
            return request_id, {"kind": "no_invite"}
        return request_id, {"kind": "link", "token": token, "code": code,
                            "new": account is None}

    def pending_request(self, request_id: str) -> dict | None:
        row = self.store.one("SELECT * FROM email_requests WHERE id=?", (request_id,))
        return dict(row) if row else None

    def request_for_token(self, token: str) -> dict | None:
        if not token or len(token) > 100:
            return None
        row = self.store.one("SELECT * FROM email_requests WHERE token_hash=?", (sha256(token),))
        if not row or row["used_at"] is not None or row["expires_at"] <= self.now():
            return None
        return dict(row)

    def redeem_token(self, token: str, agent: str = "") -> tuple[str, dict]:
        req = self.request_for_token(token)
        if req is None:
            raise SignInRefused("This sign-in link has expired or was already used.", "link_spent")
        return self._finish_email(req, agent)

    def redeem_code(self, request_id: str, code: str, agent: str = "") -> tuple[str, dict]:
        code = re.sub(r"\D", "", code or "")
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM email_requests WHERE id=?", (request_id,)).fetchone()
            if (row is None or row["code_hash"] is None or row["used_at"] is not None
                    or row["expires_at"] <= self.now()):
                raise SignInRefused("That code has expired. Ask for a new one.", "code_spent")
            if row["attempts"] >= CODE_ATTEMPTS:
                raise SignInRefused("Too many tries. Ask for a new code.", "code_spent")
            conn.execute("UPDATE email_requests SET attempts=attempts+1 WHERE id=?", (request_id,))
            ok = hmac.compare_digest(row["code_hash"], self._mac("code", f"{request_id}:{code}"))
        if not ok:
            left = CODE_ATTEMPTS - row["attempts"] - 1
            raise SignInRefused(f"That code didn't match. {left} tries left." if left > 0 else
                                "That code didn't match. Ask for a new one.", "code_wrong")
        return self._finish_email(dict(row), agent)

    def _finish_email(self, req: dict, agent: str) -> tuple[str, dict]:
        now = self.now()
        with self.store.connect() as conn:
            n = conn.execute("UPDATE email_requests SET used_at=? WHERE id=? AND used_at IS NULL"
                             " AND expires_at>?", (now, req["id"], now)).rowcount
            if n != 1:
                raise SignInRefused("This sign-in link has expired or was already used.", "link_spent")
            conn.execute("UPDATE email_requests SET used_at=? WHERE email=? AND used_at IS NULL",
                         (now, req["email"]))
            row = conn.execute("SELECT * FROM accounts WHERE email=?", (req["email"],)).fetchone()
            if row is None:
                invite = self._admit(conn, req["email"], req["invite_id"])
                account_id = self._create_account(conn, req["email"], invite, method="email")
            else:
                if row["disabled_at"] is not None:
                    raise SignInRefused("This account is switched off. Talk to a leader.", "disabled")
                account_id = row["id"]
                if req["email"] in self.cfg.leaders:
                    self._grant(conn, account_id, "leader", "config")
            session = self._open_session(conn, account_id, "email", agent)
        return session, self.account(account_id)

    # -- Google ----------------------------------------------------------
    def start_flow(self, invite_code: str | None) -> dict:
        from .oidc import pkce_pair
        verifier, challenge = pkce_pair()
        invite_state = self.invite_by_code(invite_code) if invite_code else None
        flow = {"id": secrets.token_urlsafe(24), "state": secrets.token_urlsafe(24),
                "nonce": secrets.token_urlsafe(24), "verifier": verifier,
                "challenge": challenge,
                "invite_id": invite_state.invite["id"] if invite_state and invite_state.invite else None}
        self.store.run("INSERT INTO oidc_flows(id, state, nonce, verifier, invite_id, created_at)"
                       " VALUES (?,?,?,?,?,?)", (sha256(flow["id"]), flow["state"], flow["nonce"],
                                                 verifier, flow["invite_id"], self.now()))
        return flow

    def take_flow(self, flow_cookie: str, state: str) -> dict | None:
        """The flow this browser started, used once, if `state` matches."""
        if not flow_cookie or not state:
            return None
        now = self.now()
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM oidc_flows WHERE id=?", (sha256(flow_cookie),)).fetchone()
            if (row is None or row["used_at"] is not None or row["created_at"] + FLOW_SECONDS < now
                    or not hmac.compare_digest(row["state"], state)):
                return None
            conn.execute("UPDATE oidc_flows SET used_at=? WHERE id=?", (now, row["id"]))
        return dict(row)

    def finish_google(self, claims: dict, invite_id: str | None, agent: str = "") -> tuple[str, dict]:
        email = normalize_email(claims["email"])
        if email is None:
            raise SignInRefused("Google gave an email address we can't use.", "bad_email")
        sub = claims["sub"]
        name = " ".join(str(claims.get("name", "")).split())[:60] or None
        now = self.now()
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM accounts WHERE google_sub=?", (sub,)).fetchone()
            if row is None:
                row = conn.execute("SELECT * FROM accounts WHERE email=?", (email,)).fetchone()
                if row is not None:
                    if row["google_sub"] and row["google_sub"] != sub:
                        raise SignInRefused("This email is already joined to a different Google "
                                            "account. Use that one, or the emailed link.", "sub_clash")
                    conn.execute("UPDATE accounts SET google_sub=?, updated_at=? WHERE id=?",
                                 (sub, now, row["id"]))
                    self.store.event(conn, now, "account.linked", row["id"], method="google")
            if row is None:
                invite = self._admit(conn, email, invite_id)
                account_id = self._create_account(conn, email, invite, google_sub=sub,
                                                  suggested_name=name, method="google")
            else:
                if row["disabled_at"] is not None:
                    raise SignInRefused("This account is switched off. Talk to a leader.", "disabled")
                account_id = row["id"]
                if email in self.cfg.leaders:
                    self._grant(conn, account_id, "leader", "config")
            session = self._open_session(conn, account_id, "google", agent)
        return session, self.account(account_id)

    # -- sessions --------------------------------------------------------
    def _open_session(self, conn, account_id: str, method: str, agent: str) -> str:
        token, now = secrets.token_urlsafe(32), self.now()
        conn.execute(
            "INSERT INTO sessions(id_hash, account_id, method, created_at, last_seen, expires_at,"
            " user_agent) VALUES (?,?,?,?,?,?,?)",
            (sha256(token), account_id, method, now, now, now + self.cfg.session_days * 86400,
             (agent or "")[:120]))
        self.store.event(conn, now, "account.signed_in", account_id, method=method)
        return token

    def session_account(self, token: str) -> dict | None:
        if not token or len(token) > 100:
            return None
        now = self.now()
        row = self.store.one(
            "SELECT s.id_hash, s.last_seen, s.expires_at, s.revoked_at, a.* FROM sessions s"
            " JOIN accounts a ON a.id=s.account_id WHERE s.id_hash=?", (sha256(token),))
        if (row is None or row["revoked_at"] is not None or row["expires_at"] <= now
                or row["last_seen"] + self.cfg.session_idle_days * 86400 <= now
                or row["disabled_at"] is not None):
            return None
        if now - row["last_seen"] > 3600:
            self.store.run("UPDATE sessions SET last_seen=? WHERE id_hash=?", (now, row["id_hash"]))
        account = dict(row)
        for k in ("id_hash", "last_seen", "expires_at", "revoked_at"):
            account.pop(k)
        return account

    def session_method(self, token: str) -> str | None:
        row = self.store.one("SELECT method FROM sessions WHERE id_hash=?", (sha256(token),))
        return row["method"] if row else None

    def sign_out(self, token: str, everywhere: bool = False) -> None:
        now = self.now()
        with self.store.connect() as conn:
            row = conn.execute("SELECT account_id FROM sessions WHERE id_hash=?",
                               (sha256(token),)).fetchone()
            if row is None:
                return
            if everywhere:
                conn.execute("UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL",
                             (now, row["account_id"]))
            else:
                conn.execute("UPDATE sessions SET revoked_at=? WHERE id_hash=?", (now, sha256(token)))
            self.store.event(conn, now, "account.signed_out", row["account_id"], everywhere=everywhere)

    # -- rate limits -----------------------------------------------------
    def allow(self, key: str, limit: int, window: int) -> bool:
        """Fixed-window counter. False once `limit` hits land in one window."""
        now = self.now()
        start = now - now % window
        with self.store.connect() as conn:
            row = conn.execute("SELECT window, count FROM rate WHERE key=?", (key,)).fetchone()
            if row is None or row["window"] != start:
                conn.execute("INSERT INTO rate(key, window, count) VALUES (?,?,1) ON CONFLICT(key)"
                             " DO UPDATE SET window=excluded.window, count=1", (key, start))
                return True
            if row["count"] >= limit:
                return False
            conn.execute("UPDATE rate SET count=count+1 WHERE key=?", (key,))
            return True

    def sweep(self) -> None:
        """Forget spent sign-in requests, flows and old counters."""
        now = self.now()
        with self.store.connect() as conn:
            conn.execute("DELETE FROM email_requests WHERE expires_at < ?", (now - 86400,))
            conn.execute("DELETE FROM oidc_flows WHERE created_at < ?", (now - 86400,))
            conn.execute("DELETE FROM rate WHERE window < ?", (now - 2 * 86400,))
            conn.execute("DELETE FROM sessions WHERE expires_at < ? OR revoked_at < ?",
                         (now - 86400, now - 30 * 86400))
