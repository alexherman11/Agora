"""Offline protocol reference. NOT a reader, storage boundary or live connector.

No network, disk persistence, server, browser, OS guard probe or world access.
Only invented data belongs here. A future isolated reader needs separate review;
injectable Python objects cannot authenticate callers or contain same-user agents.
"""
import base64
from dataclasses import dataclass, field
import hashlib
import hmac
import secrets
from urllib.parse import parse_qs, urlencode, urlsplit

SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
AUTHORIZATION = "https://accounts.google.com/o/oauth2/v2/auth"
BLOCKED = "disabled: private reader isolation and human caller channel not deployed"


def live_request(*args, **kwargs):
    """No configuration, actor name, world prop or caller header enables this."""
    return {"schema": 1, "source": "gmail", "state": "disabled", "reason": BLOCKED,
            "unread_count": None, "visible_count": None, "last_sync": None,
            "retry_at": None, "revocation": "none", "permissions": "headers-only",
            "previews": "unavailable"}


@dataclass(repr=False)
class FakeResponse:
    status: int = 200
    data: dict = field(default_factory=dict)
    retry_after: int = 0


class ScriptedExchange:
    """Strict fake transport; deliberately has no HTTP implementation."""
    def __init__(self, responses=()):
        self.responses = list(responses)
        self.requests = []  # Invented fixture data only, never a production log.

    def exchange(self, operation, **parameters):
        if operation not in {"token", "refresh", "list", "metadata", "revoke"}:
            raise AssertionError("operation outside phase one")
        self.requests.append((operation, parameters))
        if not self.responses:
            raise AssertionError("unscripted fake operation")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@dataclass(repr=False)
class Pending:
    state: str
    verifier: str
    redirect: str
    deadline: float


class OfflineGmail:
    """Fake-only mutable model. Fields are NOT private security compartments."""
    def __init__(self, exchange, clock):
        if type(exchange) is not ScriptedExchange:
            raise TypeError("only ScriptedExchange is supported")
        self.exchange = exchange
        self.clock = clock
        self.pending = None
        self.access = self.refresh = self.revoke_pending = None
        self.expires = self.retry_at = 0
        self.failures = 0
        self.items = {}
        self.dismissed = set()
        self.last_sync = None
        self.state = "disconnected"

    @staticmethod
    def permitted(guard):
        # Values model trusted host observations, NOT fields accepted from callers.
        return guard == {"awake": True, "unlocked": True, "game": "clear"}

    def begin(self, port, guard):
        if not self.permitted(guard) or not 1024 <= port <= 65535:
            return None
        if (self.state not in {"disconnected", "permission-lost"} or self.revoke_pending
                or self.clock() < self.retry_at):
            return None
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        self.pending = Pending(secrets.token_urlsafe(32), verifier,
                               f"http://127.0.0.1:{port}/oauth/callback", self.clock() + 300)
        self.state = "connecting"
        # Returned only to a hypothetical private human UI, never the world.
        return AUTHORIZATION + "?" + urlencode({
            "client_id": "invented-desktop-client",
            "response_type": "code", "redirect_uri": self.pending.redirect,
            "scope": SCOPE, "state": self.pending.state, "code_challenge": challenge,
            "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent"})

    def callback(self, url, guard):
        p = self.pending
        if not p or not self.permitted(guard):
            return False
        if self.clock() >= p.deadline:
            self.pending = None
            self.state = "disconnected"
            return False
        try:
            u, redirect = urlsplit(url), urlsplit(p.redirect)
            q = parse_qs(u.query, keep_blank_values=True, strict_parsing=True)
            valid = (u.scheme == redirect.scheme and u.netloc == redirect.netloc
                     and u.path == redirect.path and not u.fragment
                     and set(q) in ({"state", "code"}, {"state", "error"})
                     and all(len(v) == 1 and v[0] for v in q.values())
                     and hmac.compare_digest(q["state"][0], p.state))
        except (ValueError, KeyError):
            valid = False
        if not valid:
            return False
        self.pending = None  # One attempt, consumed before token exchange.
        self.state = "disconnected"
        if "error" in q:
            return False
        response = self.call("token", code=q["code"][0], code_verifier=p.verifier,
                             redirect_uri=p.redirect, client_id="invented-desktop-client",
                             grant_type="authorization_code")
        result = self.tokens(response, initial=True)
        if not result and self.state == "delayed":
            self.state = "disconnected"  # Consumed code: a new explicit flow after backoff.
        return result

    def call(self, operation, **parameters):
        try:
            return self.exchange.exchange(operation, **parameters)
        except Exception:
            # Never echo exception text: it may contain tokens, URLs or headers.
            return FakeResponse(503)

    def lost(self):
        self.pending = None
        self.access = self.refresh = None
        self.items.clear()
        self.dismissed.clear()
        self.last_sync = None
        self.state = "permission-lost"

    def failed(self, response):
        if (response.status == 401 or response.data.get("error") == "invalid_grant"
                or (response.status == 403
                    and response.data.get("reason") not in {"rateLimitExceeded", "userRateLimitExceeded"})):
            self.lost()
        else:
            self.failures += 1
            delay = min(3600, max(2 ** min(self.failures, 10), response.retry_after))
            self.retry_at = self.clock() + delay
            self.state = "delayed"
        return False

    def tokens(self, response, initial=False):
        if response.status != 200:
            return self.failed(response)
        d = response.data
        scope = d.get("scope", "" if initial else SCOPE)
        if (not isinstance(scope, str) or set(scope.split()) != {SCOPE}
                or not isinstance(d.get("token_type"), str) or d["token_type"].lower() != "bearer"
                or not isinstance(d.get("access_token"), str) or not d["access_token"]
                or type(d.get("expires_in")) is not int or d["expires_in"] <= 0
                or ("refresh_token" in d and not isinstance(d["refresh_token"], str))
                or (initial and not d.get("refresh_token"))):
            self.lost()
            return False
        self.access = d["access_token"]
        self.refresh = d.get("refresh_token") or self.refresh
        self.expires = self.clock() + d["expires_in"]
        self.state = "connected"
        return True

    def sync(self, guard):
        try:
            return self._sync(guard)
        except (TypeError, ValueError, KeyError, AttributeError):
            return self.failed(FakeResponse(502))

    def _sync(self, guard):
        if (not self.permitted(guard) or not self.refresh
                or self.clock() < self.retry_at):
            return False
        if self.clock() >= self.expires - 30:
            response = self.call("refresh", refresh_token=self.refresh,
                                 client_id="invented-desktop-client", grant_type="refresh_token")
            if not self.tokens(response):
                return False
        # Bounded full Inbox reconciliation; no history cursor or q search.
        # Commit only a complete snapshot. Partial/failed pages do not erase inbox.
        snapshot, page, pages = {}, None, set()
        for _ in range(100):
            response = self.call("list", access_token=self.access, user_id="me",
                                 labelIds=["INBOX"], maxResults=100, pageToken=page)
            if response.status != 200:
                return self.failed(response)
            for message in response.data.get("messages", []):
                key = message.get("id")
                if not isinstance(key, str) or not key or key in snapshot:
                    continue
                metadata = self.call("metadata", access_token=self.access, user_id="me",
                                     id=key, format="metadata",
                                     metadataHeaders=["From", "Subject", "Date"],
                                     fields="id,labelIds,payload/headers,internalDate")
                if metadata.status != 200:
                    return self.failed(metadata)
                d = metadata.data
                if d.get("id") != key:
                    return self.failed(FakeResponse(502))
                labels = d.get("labelIds", [])
                if "INBOX" not in labels:  # May have moved since list.
                    continue
                headers = {h["name"].lower(): h.get("value", "")
                           for h in d.get("payload", {}).get("headers", [])
                           if h.get("name", "").lower() in {"from", "subject", "date"}}
                # Do not retain body, snippet, attachment or arbitrary API fields.
                snapshot[key] = {"headers": headers, "unread": "UNREAD" in labels,
                                 "time": d.get("internalDate")}
            page = response.data.get("nextPageToken")
            if not page:
                self.items = snapshot
                self.last_sync = self.clock()
                self.state = "connected"
                self.retry_at = self.failures = 0
                return True
            if page in pages:
                break
            pages.add(page)
        return self.failed(FakeResponse(502))

    def dismiss(self, key, dismissed=True):
        # Local-only. No mark-read/modify operation exists.
        if key in self.items:
            if dismissed:
                self.dismissed.add(key)
            else:
                self.dismissed.discard(key)

    def disconnect(self, guard):
        token = self.refresh or self.access or self.revoke_pending
        self.access = self.refresh = self.pending = None
        self.items.clear()
        self.dismissed.clear()
        self.last_sync = None
        self.expires = self.retry_at = 0
        self.state = "disconnected"
        self.revoke_pending = token
        if token and self.permitted(guard):
            response = self.call("revoke", token=token)
            if response.status == 200:
                self.revoke_pending = None
        return self.revoke_pending is None

    def public_status(self):
        """Count/status whitelist; no account label, private key or supplied text."""
        connected = self.state in {"connected", "delayed"}
        return {"schema": 1, "source": "gmail", "state": self.state,
                "unread_count": sum(x["unread"] for x in self.items.values()) if connected else None,
                "visible_count": sum(k not in self.dismissed for k in self.items) if connected else None,
                "last_sync": self.last_sync, "retry_at": self.retry_at or None,
                "revocation": "pending" if self.revoke_pending else "none",
                "permissions": "headers-only", "previews": "unavailable"}
