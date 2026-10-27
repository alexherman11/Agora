"""The seam to the kernel: what a verified account hands over, and who may.

See SEAM.md. Sign-in says who you are; the kernel says what you may do. Until
the kernel exists, `may` answers from the local roles table, and that table
is the only power this service holds.
"""

from __future__ import annotations

import hmac
import json

from .config import is_loopback_host

# Words this service asks about. When the kernel exists they become entries in
# its dictionary and `may` asks the kernel instead.
LEADER_WORDS = frozenset({"invite.list", "invite.make", "invite.freeze", "site.public_invite"})


def may(app, account: dict, word: str) -> bool:
    if word in LEADER_WORDS:
        return "leader" in app.service.roles(account["id"])
    return False


def account_record(app, account: dict) -> dict:
    """The verified account, in the shape the kernel receives (SEAM.md)."""
    svc = app.service
    invite = svc.invite_by_id(account["invite_id"]).invite if account["invite_id"] else None
    methods = ["email"] + (["google"] if account["google_sub"] else [])
    return {
        "account_id": account["id"],
        "email": account["email"],
        "email_verified": bool(account["email_verified"]),
        "display_name": account["display_name"],
        "answers": svc.answers(account["id"]),
        "questions_version": app.questions.version,
        "onboarded": account["onboarded_at"] is not None,
        "disabled": account["disabled_at"] is not None,
        "created_at": account["created_at"],
        "invited_through": None if invite is None else {
            "invite_id": invite["id"], "channel": invite["channel"],
            "maker_account_id": invite["maker_id"]},
        "methods": methods,
        "issuer": app.cfg.base_url,
    }


class Seam:
    def __init__(self, app):
        self.app = app

    def _trusted(self, req) -> bool:
        secret = self.app.cfg.kernel_secret
        if not secret or not is_loopback_host(req.environ.get("REMOTE_ADDR", "")):
            return False
        given = req.header("X-Kernel-Secret")  # the kernel's header (research/kernel-lab/kernel/door.py)
        return hmac.compare_digest(given.encode(), secret.encode())

    def _deny(self):
        from .web import Response
        return Response.json({"error": "not trusted"}, "403 Forbidden")

    def session_check(self, req):
        """POST {"token": "<session cookie value>"} -> {"account", "method", "agent", "record"}.

        `account` is the account id (null when the session is unknown, ended or
        its account switched off), `method` how this session signed in, `agent`
        always null for now (agent sessions do not exist yet), and `record` the
        verified account in full.
        """
        from .web import Response
        if not self._trusted(req):
            return self._deny()
        try:
            body = json.loads(req.get("_json") or "{}")
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        token = str(body.get("token", ""))
        account = self.app.service.session_account(token)
        if account is None:
            return Response.json({"account": None, "method": None, "agent": None, "record": None})
        return Response.json({"account": account["id"], "method": self.app.service.session_method(token),
                              "agent": None, "record": account_record(self.app, account)})

    def account(self, req, account_id: str):
        from .web import Response
        if not self._trusted(req):
            return self._deny()
        account = self.app.service.account(account_id)
        if account is None:
            return Response.json({"error": "no such account"}, "404 Not Found")
        return Response.json({"account": account_record(self.app, account)})

    def events(self, req):
        """GET ?after=<seq>&limit=<n> -> account and invite events, oldest first."""
        from .web import Response
        if not self._trusted(req):
            return self._deny()
        try:
            after = int(req.query.get("after", "0"))
            limit = max(1, min(500, int(req.query.get("limit", "100"))))
        except ValueError:
            return Response.json({"error": "after and limit are numbers"}, "400 Bad Request")
        rows = self.app.store.all("SELECT * FROM events WHERE seq>? ORDER BY seq LIMIT ?", (after, limit))
        return Response.json({"events": [
            {"seq": r["seq"], "at": r["at"], "kind": r["kind"], "account_id": r["account_id"],
             "data": json.loads(r["data"])} for r in rows]})
