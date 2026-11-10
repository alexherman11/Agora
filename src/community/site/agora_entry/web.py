"""The entry service over HTTP: a plain WSGI application, no framework.

Pages are server-rendered HTML that work with no JavaScript at all. Every
POST needs a CSRF token and a same-origin Origin header when the browser
sends one; cookies are HttpOnly and SameSite=Lax, and `__Host-` prefixed and
Secure when the site runs on https.
"""

from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets
import time
import traceback
import urllib.parse
from pathlib import Path

from . import pages, qr
from .config import Config, is_loopback_host
from .db import Store
from .mailer import FileMailer, SmtpMailer
from .oidc import Google, OIDCError
from .questions import Questions
from .questions import load as load_questions
from .render import Safe
from .seam import Seam, may
from .service import INVITE_EXPIRY_DAYS, Service, SignInRefused, normalize_email, sha256

STATIC = Path(__file__).resolve().parent.parent / "static"
MAX_BODY = 64 * 1024

# (limit, window seconds). Defaults: each is a setting, SITE_LIMIT_<KIND>=<count>, and
# SITE_IP_LIMITS=off switches off every kind ending in _ip (config.py).
LIMITS = {
    "email_ip": (60, 3600), "email_addr": (5, 3600), "email_noinvite": (1, 86400),
    "code_ip": (30, 3600), "link_ip": (60, 3600), "google_ip": (30, 600),
    "join_ip": (300, 3600), "invite_make": (100, 86400), "page_ip": (600, 60),
    # guest passes: a meeting's whole room shares one wifi address; one invite takes ~300 a day
    "guest_ip": (80, 3600), "guest_invite": (300, 86400),
}


class Request:
    def __init__(self, environ: dict, cfg: Config):
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO") or "/"
        self.query = dict(urllib.parse.parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True))
        self.cookies = _parse_cookies(environ.get("HTTP_COOKIE", ""))
        self.cfg = cfg
        self._form: dict[str, list[str]] | None = None
        self.account: dict | None = None
        self.session_token: str | None = None
        self.new_cookies: list[str] = []

    def form(self) -> dict[str, list[str]]:
        if self._form is None:
            self._form = {}
            if self.method == "POST":
                try:
                    size = int(self.environ.get("CONTENT_LENGTH") or 0)
                except ValueError:
                    size = 0
                if 0 < size <= MAX_BODY:
                    body = self.environ["wsgi.input"].read(size)
                    ctype = self.environ.get("CONTENT_TYPE", "")
                    if ctype.startswith("application/x-www-form-urlencoded"):
                        for k, v in urllib.parse.parse_qsl(body.decode("utf-8", "replace"),
                                                           keep_blank_values=True):
                            self._form.setdefault(k, []).append(v)
                    elif ctype.startswith("application/json"):
                        self._form["_json"] = [body.decode("utf-8", "replace")]
        return self._form

    def get(self, name: str, default: str = "") -> str:
        values = self.form().get(name)
        return values[0] if values else default

    def getall(self, name: str) -> list[str]:
        return self.form().get(name, [])

    def header(self, name: str) -> str:
        return self.environ.get("HTTP_" + name.upper().replace("-", "_"), "")

    @property
    def ip(self) -> str:
        if self.cfg.proxy_ip_header:
            forwarded = self.header(self.cfg.proxy_ip_header).strip()
            if forwarded:
                return forwarded[:64]
        return self.environ.get("REMOTE_ADDR", "?")

    @property
    def agent(self) -> str:
        return self.header("User-Agent")[:120]


def _parse_cookies(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in raw.split(";"):
        name, sep, value = part.strip().partition("=")
        if sep and name and name not in out:
            out[name] = value.strip().strip('"')
    return out


class Response:
    def __init__(self, body: str | bytes = b"", status: str = "200 OK",
                 ctype: str = "text/html; charset=utf-8"):
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.status = status
        self.headers: list[tuple[str, str]] = [("Content-Type", ctype)]
        self.cacheable = False

    @classmethod
    def redirect(cls, location: str, status: str = "303 See Other") -> Response:
        r = cls(b"", status)
        r.headers.append(("Location", location))
        return r

    @classmethod
    def json(cls, obj, status: str = "200 OK") -> Response:
        return cls(json.dumps(obj, sort_keys=True), status, "application/json")


class App:
    def __init__(self, cfg: Config, clock=time.time, mailer=None, google: Google | None = None):
        self.cfg = cfg
        self.clock = clock
        self.store = Store(cfg.data_dir / "entry.sqlite3")
        self.questions: Questions = load_questions(cfg.content_dir / "questions.json")
        self.content = json.loads((cfg.content_dir / "site.json").read_text(encoding="utf-8"))
        self.privacy = json.loads((cfg.content_dir / "privacy.json").read_text(encoding="utf-8"))
        self.service = Service(cfg, self.store, self.questions, clock)
        unknown = set(cfg.limit_overrides) - set(LIMITS)
        if unknown:
            raise ValueError(f"unknown SITE_LIMIT_ settings: {', '.join(sorted(unknown))}")
        self.limits = {k: (cfg.limit_overrides.get(k, n), w) for k, (n, w) in LIMITS.items()}
        if mailer is not None:
            self.mailer = mailer
        elif cfg.email_mode == "off":
            self.mailer = None  # live mode before SMTP is set up: email sign-in says so
        elif cfg.email_mode == "file":
            self.mailer = FileMailer(cfg.data_dir / "outbox", cfg.email_from)
        else:
            self.mailer = SmtpMailer(cfg.smtp_host, cfg.smtp_port, cfg.smtp_user,
                                     cfg.smtp_password, cfg.email_from)
        self.google = google if google is not None else (
            Google(cfg, clock) if cfg.google_mode in ("real", "fake") else None)
        self.seam = Seam(self)
        self.pages = pages.Pages(self)
        prefix = "__Host-" if cfg.secure_cookies else ""
        self.cookie = {k: prefix + "entry_" + k for k in ("csrf", "pending", "flow", "guest")}
        self.cookie["sid"] = prefix + "agora_session"  # the kernel reads this one too (SEAM.md)
        self.routes = [
            ("GET", r"/", self.root),
            ("GET", r"/about", self.public),
            ("GET", r"/join/(?P<code>[A-Za-z0-9]{1,40})", self.join),
            ("POST", r"/join/(?P<code>[A-Za-z0-9]{1,40})/guest", self.join_guest),
            ("GET", r"/join", self.join_public),
            ("GET", r"/privacy", lambda req: self.pages.privacy(req)),
            ("GET", r"/signin", self.signin),
            ("POST", r"/signin/email", self.signin_email),
            ("GET", r"/signin/check", self.signin_check),
            ("POST", r"/signin/code", self.signin_code),
            ("GET", r"/signin/link", self.signin_link),
            ("POST", r"/signin/link", self.signin_link_post),
            ("GET", r"/auth/google/start", self.google_start),
            ("GET", r"/auth/google/callback", self.google_callback),
            ("GET", r"/welcome", self.welcome),
            ("POST", r"/welcome", self.welcome_post),
            ("GET", r"/home", self.home),
            ("GET", r"/account", self.account_page),
            ("POST", r"/account", self.account_post),
            ("POST", r"/signout", self.signout),
            ("GET", r"/leader/invites", self.leader_invites),
            ("POST", r"/leader/invites", self.leader_make_invite),
            ("GET", r"/leader/invites/(?P<invite_id>inv_[a-z0-9]{20})", self.leader_invite),
            ("GET", r"/leader/invites/(?P<invite_id>inv_[a-z0-9]{20})/qr", self.leader_invite_qr),
            ("POST", r"/leader/invites/(?P<invite_id>inv_[a-z0-9]{20})/"
                     r"(?P<act>freeze|unfreeze|public|unpublic|guests_on|guests_off)",
             self.leader_invite_act),
            ("GET", r"/entry-static/(?P<name>[a-z0-9_-]{1,40}\.(?:css|svg|js|png))", self.static),
            ("GET", r"/favicon\.ico", lambda req: self.static(req, "icon.svg")),
            ("GET", r"/healthz", lambda req: Response("ok", ctype="text/plain")),
            ("POST", r"/internal/session/check", self.seam.session_check),
            ("GET", r"/internal/accounts/(?P<account_id>acct_[a-z0-9]{20})", self.seam.account),
            ("GET", r"/internal/events", self.seam.events),
            ("GET", r"/dev/outbox", self.dev_outbox),
        ]
        self.routes = [(m, re.compile(p + r"\Z"), h) for m, p, h in self.routes]
        self._last_sweep = 0.0

    # -- WSGI -------------------------------------------------------------
    def __call__(self, environ, start_response):
        req = Request(environ, self.cfg)
        try:
            resp = self.dispatch(req)
        except Exception:  # noqa: BLE001 - one page must never take the site down
            traceback.print_exc()
            resp = self.pages.message(req, "Something went wrong",
                                      "Sorry, that didn't work. Please try again in a moment.",
                                      status="500 Internal Server Error")
        headers = list(resp.headers) + [("Set-Cookie", c) for c in req.new_cookies]
        headers += self.security_headers(resp)
        headers.append(("Content-Length", str(len(resp.body))))
        start_response(resp.status, headers)
        return [resp.body if req.method != "HEAD" else b""]

    def security_headers(self, resp: Response) -> list[tuple[str, str]]:
        h = [
            ("Content-Security-Policy", "default-src 'none'; style-src 'self'; img-src 'self' data:; "
                                        "script-src 'self'; form-action 'self'; frame-ancestors 'none'; "
                                        "base-uri 'none'"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("X-Frame-Options", "DENY"),
            ("Cross-Origin-Opener-Policy", "same-origin"),
            ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), interest-cohort=()"),
            ("Cache-Control", "public, max-age=3600" if resp.cacheable else "no-store"),
        ]
        if self.cfg.secure_cookies:
            h.append(("Strict-Transport-Security", "max-age=31536000"))
        return h

    def dispatch(self, req: Request) -> Response:
        if self.clock() - self._last_sweep > 3600:
            self._last_sweep = self.clock()
            self.service.sweep()
        method = "GET" if req.method == "HEAD" else req.method
        host = req.header("Host")
        if (host and host != urllib.parse.urlsplit(self.cfg.base_url).netloc and method == "GET"
                and not req.path.startswith(("/internal/", "/healthz"))):
            # One address only, so cookies, the Origin check and Google's redirect all agree.
            query = req.environ.get("QUERY_STRING", "")
            return Response.redirect(self.cfg.base_url + req.path + (f"?{query}" if query else ""),
                                     "308 Permanent Redirect")
        token = req.cookies.get(self.cookie["sid"])
        if token:
            req.account = self.service.session_account(token)
            req.session_token = token if req.account else None
        path_matched = False
        for m, pattern, handler in self.routes:
            match = pattern.match(req.path)
            if not match:
                continue
            path_matched = True
            if m != method:
                continue
            if method == "POST" and not req.path.startswith("/internal/") and not self.csrf_ok(req):
                return self.pages.message(
                    req, "Please try that again",
                    "This page was open for a while, so we couldn't be sure the form came from you. "
                    "Go back, refresh, and try once more.", status="403 Forbidden")
            return handler(req, **match.groupdict())
        if path_matched:
            return Response("Method not allowed", "405 Method Not Allowed", "text/plain")
        return self.pages.message(req, "Not here", "There's no page at this address.",
                                  status="404 Not Found")

    # -- cookies and CSRF ---------------------------------------------------
    def set_cookie(self, req: Request, key: str, value: str, max_age: int) -> None:
        parts = [f"{self.cookie[key]}={value}", "Path=/", f"Max-Age={max_age}", "HttpOnly",
                 "SameSite=Lax"]
        if self.cfg.secure_cookies:
            parts.append("Secure")
        req.new_cookies.append("; ".join(parts))

    def clear_cookie(self, req: Request, key: str) -> None:
        self.set_cookie(req, key, "", 0)

    def csrf_token(self, req: Request) -> str:
        seed = req.cookies.get(self.cookie["csrf"])
        if not seed or not re.fullmatch(r"[A-Za-z0-9_-]{20,64}", seed):
            seed = secrets.token_urlsafe(24)
            req.cookies[self.cookie["csrf"]] = seed
            self.set_cookie(req, "csrf", seed, 60 * 60 * 24 * 365)
        return hmac.new(self.cfg.secret_key, f"csrf:{seed}".encode(), "sha256").hexdigest()

    def csrf_ok(self, req: Request) -> bool:
        origin = req.header("Origin")
        if origin and origin != "null" and origin != self.cfg.base_origin:
            return False
        seed = req.cookies.get(self.cookie["csrf"])
        if not seed:
            return False
        expected = hmac.new(self.cfg.secret_key, f"csrf:{seed}".encode(), "sha256").hexdigest()
        return hmac.compare_digest(expected, req.get("csrf"))

    def allow(self, kind: str, who: str) -> bool:
        if kind.endswith("_ip") and not self.cfg.ip_limits:
            return True
        limit, window = self.limits[kind]
        return self.service.allow(f"{kind}:{sha256(who)[:32]}", limit, window)

    def start_session(self, req: Request, token: str, account: dict) -> Response:
        self.set_cookie(req, "sid", token, self.cfg.session_days * 86400)
        self.clear_cookie(req, "pending")
        self.clear_cookie(req, "flow")
        if req.cookies.get(self.cookie["guest"]):
            self.clear_cookie(req, "guest")  # kept as this account now, or another account chosen
        if account.get("upgraded"):
            # Same account id, so the kernel's person stays; tell it about the new standing.
            self.service.kernel_join(account["id"])
        return Response.redirect(self.cfg.home_path if account["onboarded_at"] else "/welcome")

    def guest_claim(self, req: Request) -> str | None:
        return req.cookies.get(self.cookie["guest"]) or None

    def is_guest(self, account: dict | None) -> bool:
        return bool(account and account.get("guest_until") is not None)

    def need_account(self, req: Request) -> Response | None:
        if req.account is None:
            return Response.redirect("/signin")
        return None

    # -- public pages ---------------------------------------------------------
    def root(self, req: Request) -> Response:
        # The board (the kernel) is the landing page at /; the proxy sends / there. Run alone,
        # this service points / at the mission page, or home for someone signed in.
        if self.cfg.home_path != "/" and req.account:
            return Response.redirect(self.cfg.home_path)
        return Response.redirect("/home" if req.account else "/about")

    def public(self, req: Request) -> Response:
        if not self.allow("page_ip", req.ip):
            return self.pages.too_many(req)
        return self.pages.public(req)

    def join_public(self, req: Request) -> Response:
        state = self.service.public_invite()
        if state and state.open:
            return Response.redirect("/join/" + state.invite["code"])
        return self.pages.message(req, "Joining is by invite",
                                  self.content["join"]["no_invite"], back=("/", "Back to the front page"))

    def join(self, req: Request, code: str) -> Response:
        if not self.allow("join_ip", req.ip):
            return self.pages.too_many(req)
        state = self.service.invite_by_code(code)
        if req.account:
            return Response.redirect(self.cfg.home_path)
        if not state.open:
            return self.pages.invite_closed(req, state)
        maker = self.service.account(state.invite["maker_id"])
        if state.invite["guest_ok"] and req.query.get("account") != "1":
            return self.pages.join_guest(req, state.invite, maker)
        return self.pages.join(req, state.invite, maker)

    def join_guest(self, req: Request, code: str) -> Response:
        if req.account:
            return Response.redirect(self.cfg.home_path)
        state = self.service.invite_by_code(code)
        if not state.open:
            return self.pages.invite_closed(req, state)
        if not state.invite["guest_ok"]:
            return Response.redirect(f"/join/{state.invite['code']}?account=1")
        maker = self.service.account(state.invite["maker_id"])
        name = req.get("name")
        if not self.allow("guest_ip", req.ip) or not self.allow("guest_invite", state.invite["id"]):
            return self.pages.too_many(req)
        try:
            token, claim, account = self.service.create_guest(code, name, req.agent)
        except SignInRefused as refused:
            if refused.kind == "bad_name":
                return self.pages.join_guest(req, state.invite, maker, name=name, error=refused.reason)
            return self.pages.refused(req, refused)
        now = self.service.now()
        self.set_cookie(req, "sid", token, max(60, account["guest_until"] - now))
        # A separate, longer-lived claim: this browser may later keep this account with an email.
        self.set_cookie(req, "guest", claim,
                        max(60, account["guest_until"] + self.cfg.guest_claim_days * 86400 - now))
        self.service.kernel_join(account["id"])
        return Response.redirect(self.cfg.home_path)

    def signin(self, req: Request) -> Response:
        if req.account and not self.is_guest(req.account):
            return Response.redirect(self.cfg.home_path)
        return self.pages.signin(req)

    def signin_email(self, req: Request) -> Response:
        email = normalize_email(req.get("email"))
        invite_code = req.get("invite")[:40] or None
        if email is None:
            return self.pages.signin(req, invite_code=invite_code, email=req.get("email"),
                                     error="That doesn't look like an email address. Check it and try again.")
        if self.mailer is None:
            return self.pages.no_email(req)
        if not self.allow("email_ip", req.ip) or not self.allow("email_addr", email):
            return self.pages.too_many(req)
        request_id, send = self.service.request_email_signin(email, invite_code, self.guest_claim(req))
        self.send_signin_email(email, send)
        self.set_cookie(req, "pending", request_id, self.cfg.link_minutes * 60 + 300)
        return Response.redirect("/signin/check")

    def send_signin_email(self, email: str, send: dict) -> None:
        kind = send["kind"]
        if kind == "none":
            return
        if kind in ("no_invite", "invite_closed") and not self.allow("email_noinvite", email):
            return
        subject, text, html_body, links = pages.signin_email(self, send)
        self.mailer.send(email, subject, text, html_body, links)

    def signin_check(self, req: Request) -> Response:
        pending = self.service.pending_request(req.cookies.get(self.cookie["pending"], ""))
        if pending is None:
            return Response.redirect("/signin")
        return self.pages.check(req, pending["email"])

    def signin_code(self, req: Request) -> Response:
        request_id = req.cookies.get(self.cookie["pending"], "")
        pending = self.service.pending_request(request_id)
        if pending is None:
            return Response.redirect("/signin")
        if not self.allow("code_ip", req.ip):
            return self.pages.too_many(req)
        try:
            token, account = self.service.redeem_code(request_id, req.get("code"), req.agent,
                                                      self.guest_claim(req))
        except SignInRefused as refused:
            if refused.kind == "code_wrong":
                return self.pages.check(req, pending["email"], error=refused.reason)
            return self.pages.refused(req, refused)
        return self.start_session(req, token, account)

    def signin_link(self, req: Request) -> Response:
        if not self.allow("link_ip", req.ip):
            return self.pages.too_many(req)
        token = req.query.get("t", "")
        found = self.service.request_for_token(token)
        if found is None:
            return self.pages.refused(req, SignInRefused(
                "This sign-in link has expired or was already used.", "link_spent"))
        # A button, not an automatic sign-in: mail scanners open links too.
        # A link with no code (minted by the CLI) has no waiting tab to warn about.
        elsewhere = found["code_hash"] is not None and req.cookies.get(self.cookie["pending"]) != found["id"]
        return self.pages.link_confirm(req, token, found["email"], elsewhere)

    def signin_link_post(self, req: Request) -> Response:
        if not self.allow("link_ip", req.ip):
            return self.pages.too_many(req)
        try:
            token, account = self.service.redeem_token(req.get("t"), req.agent, self.guest_claim(req))
        except SignInRefused as refused:
            return self.pages.refused(req, refused)
        return self.start_session(req, token, account)

    def google_start(self, req: Request) -> Response:
        if self.google is None:
            return self.pages.message(req, "Not available yet",
                                      "Continue with Google isn't switched on yet. Use your email instead.",
                                      back=("/signin", "Sign in with email"), status="404 Not Found")
        if not self.allow("google_ip", req.ip):
            return self.pages.too_many(req)
        flow = self.service.start_flow(req.query.get("invite", "")[:40] or None)
        self.set_cookie(req, "flow", flow["id"], 600)
        return Response.redirect(self.google.authorize_url(flow["state"], flow["nonce"], flow["challenge"]))

    def google_callback(self, req: Request) -> Response:
        if self.google is None:
            return Response.redirect("/signin")
        if not self.allow("google_ip", req.ip):
            return self.pages.too_many(req)
        flow = self.service.take_flow(req.cookies.get(self.cookie["flow"], ""), req.query.get("state", ""))
        self.clear_cookie(req, "flow")
        if flow is None:
            return self.pages.message(req, "Let's try that again",
                                      "That sign-in took too long or started in another browser. "
                                      "Start again from here.", back=("/signin", "Sign in"),
                                      status="400 Bad Request")
        if req.query.get("error") or not req.query.get("code"):
            return self.pages.message(req, "Google sign-in was cancelled",
                                      "No problem. You can try again, or use your email instead.",
                                      back=("/signin", "Back to sign in"))
        try:
            id_token = self.google.exchange(req.query["code"], flow["verifier"])
            claims = self.google.verify(id_token, flow["nonce"])
        except OIDCError as exc:
            print(f"google sign-in refused: {exc}")
            return self.pages.message(req, "Google sign-in didn't work",
                                      "Something went wrong talking to Google. Try again, or use your "
                                      "email instead.", back=("/signin", "Back to sign in"),
                                      status="502 Bad Gateway")
        try:
            token, account = self.service.finish_google(claims, flow["invite_id"], req.agent,
                                                        self.guest_claim(req))
        except SignInRefused as refused:
            return self.pages.refused(req, refused)
        return self.start_session(req, token, account)

    # -- after sign-in ----------------------------------------------------------
    def welcome(self, req: Request) -> Response:
        if (r := self.need_account(req)) is not None:
            return r
        if req.account["onboarded_at"]:
            return Response.redirect(self.cfg.home_path)
        return self.pages.welcome(req)

    def read_answers(self, req: Request) -> tuple[dict, dict, str]:
        values, errors = {}, {}
        for q in self.questions.questions:
            raw = req.getall("q_" + q.key) if q.type == "choices" else req.get("q_" + q.key)
            value, problem = q.clean(raw)
            values[q.key] = value
            if problem:
                errors[q.key] = problem
        return values, errors, values.get("display_name", "")

    def welcome_post(self, req: Request) -> Response:
        if (r := self.need_account(req)) is not None:
            return r
        values, errors, name = self.read_answers(req)
        if errors:
            return self.pages.welcome(req, values=values, errors=errors)
        self.service.save_answers(req.account["id"], values, name)
        self.service.kernel_join(req.account["id"])
        return Response.redirect(self.cfg.home_path)

    def home(self, req: Request) -> Response:
        if (r := self.need_account(req)) is not None:
            return r
        if not req.account["onboarded_at"]:
            return Response.redirect("/welcome")
        if self.cfg.kernel_url and not req.account["kernel_person"]:
            self.service.kernel_join(req.account["id"])  # the kernel was away, or said no: ask again
            req.account = self.service.session_account(req.session_token) or req.account
        return self.pages.home(req)

    def account_page(self, req: Request) -> Response:
        if (r := self.need_account(req)) is not None:
            return r
        return self.pages.account(req, saved=req.query.get("saved") == "1")

    def account_post(self, req: Request) -> Response:
        if (r := self.need_account(req)) is not None:
            return r
        values, errors, name = self.read_answers(req)
        if errors:
            return self.pages.account(req, values=values, errors=errors)
        self.service.save_answers(req.account["id"], values, name)
        return Response.redirect("/account?saved=1")

    def signout(self, req: Request) -> Response:
        if req.session_token:
            self.service.sign_out(req.session_token, everywhere=req.get("everywhere") == "1")
        self.clear_cookie(req, "sid")
        if req.cookies.get(self.cookie["guest"]):
            self.clear_cookie(req, "guest")  # a shared phone: the next person can't keep this pass
        return Response.redirect("/")

    # -- leaders --------------------------------------------------------------
    def need_word(self, req: Request, word: str) -> Response | None:
        if req.account is None:
            return Response.redirect("/signin")
        if not may(self, req.account, word):
            return self.pages.message(req, "Not for this account",
                                      "Only group leaders can do this.", back=("/home", "Back"),
                                      status="403 Forbidden")
        return None

    def leader_invites(self, req: Request) -> Response:
        if (r := self.need_word(req, "invite.list")) is not None:
            return r
        return self.pages.leader_invites(req)

    def leader_make_invite(self, req: Request) -> Response:
        if (r := self.need_word(req, "invite.make")) is not None:
            return r
        if not self.allow("invite_make", req.account["id"]):
            return self.pages.too_many(req)
        kind = req.get("kind", "link")
        raw_uses = req.get("max_uses").strip()
        try:
            max_uses = int(raw_uses) if raw_uses else None
            days = int(req.get("expires_days") or (1 if kind == "event" else 30))
            invite = self.service.make_invite(req.account["id"], req.get("channel"), kind,
                                              max_uses, days, guest_ok=req.get("guest_ok") == "1")
        except ValueError as exc:
            message = str(exc) if "invalid literal" not in str(exc) else "Uses must be a whole number."
            return self.pages.leader_invites(req, error=message, form=req.form())
        return Response.redirect(f"/leader/invites/{invite['id']}")

    def leader_invite(self, req: Request, invite_id: str) -> Response:
        if (r := self.need_word(req, "invite.list")) is not None:
            return r
        state = self.service.invite_by_id(invite_id)
        if state.invite is None:
            return self.pages.message(req, "No such invite", "That invite doesn't exist.",
                                      back=("/leader/invites", "All invites"), status="404 Not Found")
        return self.pages.leader_invite(req, state)

    def leader_invite_qr(self, req: Request, invite_id: str) -> Response:
        if (r := self.need_word(req, "invite.list")) is not None:
            return r
        state = self.service.invite_by_id(invite_id)
        if state.invite is None:
            return Response.redirect("/leader/invites")
        return self.pages.invite_qr(req, state)

    def leader_invite_act(self, req: Request, invite_id: str, act: str) -> Response:
        word = "site.public_invite" if act in ("public", "unpublic") else "invite.freeze"
        if (r := self.need_word(req, word)) is not None:
            return r
        if self.service.invite_by_id(invite_id).invite is None:
            return Response.redirect("/leader/invites")
        if act in ("freeze", "unfreeze"):
            self.service.set_frozen(invite_id, req.account["id"], act == "freeze")
        elif act in ("guests_on", "guests_off"):
            self.service.set_guest_ok(invite_id, req.account["id"], act == "guests_on")
        else:
            self.service.set_public_invite(invite_id if act == "public" else None, req.account["id"])
        return Response.redirect(f"/leader/invites/{invite_id}")

    # -- files and test-mode helpers ------------------------------------------
    def static(self, req: Request, name: str) -> Response:
        path = STATIC / name
        if not path.is_file():
            return Response("not found", "404 Not Found", "text/plain")
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript") or ctype.endswith("svg+xml"):
            ctype += "; charset=utf-8"
        resp = Response(path.read_bytes(), ctype=ctype)
        resp.cacheable = True
        return resp

    def dev_outbox(self, req: Request) -> Response:
        remote = req.environ.get("REMOTE_ADDR", "")
        if not self.cfg.is_test or not is_loopback_host(remote) or not hasattr(self.mailer, "recent"):
            return self.pages.message(req, "Not here", "There's no page at this address.",
                                      status="404 Not Found")
        return self.pages.outbox(req, self.mailer.recent())

    def invite_url(self, invite: dict) -> str:
        return f"{self.cfg.base_url}/join/{invite['code']}"

    def qr_svg(self, invite: dict) -> Safe:
        return Safe(qr.svg(self.invite_url(invite), title=f"QR code for {invite['channel']}"))

    def expiry_choices(self) -> tuple[int, ...]:
        return INVITE_EXPIRY_DAYS
