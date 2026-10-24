from __future__ import annotations

import hmac
import io
import re
import socket
import sys
import urllib.parse
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE))

from agora_entry.config import Config  # noqa: E402
from agora_entry.web import App  # noqa: E402

LEADER = "leader@example.com"


class Clock:
    def __init__(self, t: float = 1_790_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class Resp:
    def __init__(self, status: str, headers: list[tuple[str, str]], body: bytes):
        self.status = int(status.split()[0])
        self.headers = headers
        self.text = body.decode("utf-8", "replace")

    def header(self, name: str) -> str | None:
        return next((v for k, v in self.headers if k.lower() == name.lower()), None)

    def cookies_set(self) -> list[str]:
        return [v for k, v in self.headers if k.lower() == "set-cookie"]

    @property
    def location(self) -> str | None:
        return self.header("Location")


class Client:
    """A browser stand-in: keeps cookies, sends Origin on POST."""

    def __init__(self, app: App, remote: str = "127.0.0.1"):
        self.app, self.remote = app, remote
        self.cookies: dict[str, str] = {}

    def request(self, method: str, url: str, data=None, headers: dict | None = None,
                body: bytes | None = None, ctype: str | None = None) -> Resp:
        parts = urllib.parse.urlsplit(url)
        if body is None and data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode()
            ctype = ctype or "application/x-www-form-urlencoded"
        body = body or b""
        environ = {
            "REQUEST_METHOD": method, "PATH_INFO": parts.path, "QUERY_STRING": parts.query,
            "SERVER_NAME": "127.0.0.1", "SERVER_PORT": "8817", "REMOTE_ADDR": self.remote,
            "wsgi.input": io.BytesIO(body), "wsgi.url_scheme": "http",
            "CONTENT_LENGTH": str(len(body)), "CONTENT_TYPE": ctype or "",
            "HTTP_USER_AGENT": "pytest",
        }
        if self.cookies:
            environ["HTTP_COOKIE"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        hdrs = dict(headers or {})
        if method == "POST" and "Origin" not in hdrs:
            hdrs["Origin"] = self.app.cfg.base_origin
        for k, v in hdrs.items():
            if v is not None:
                environ["HTTP_" + k.upper().replace("-", "_")] = v
        captured = {}

        def start_response(status, response_headers):
            captured["status"], captured["headers"] = status, response_headers

        out = b"".join(self.app(environ, start_response))
        resp = Resp(captured["status"], captured["headers"], out)
        for raw in resp.cookies_set():
            name, _, rest = raw.partition("=")
            value = rest.split(";", 1)[0]
            if "Max-Age=0" in raw:
                self.cookies.pop(name, None)
            else:
                self.cookies[name] = value
        return resp

    def get(self, url: str, **kw) -> Resp:
        return self.request("GET", url, **kw)

    def csrf(self) -> str:
        name = self.app.cookie["csrf"]
        if name not in self.cookies:
            self.get("/signin")  # any page with a form sets the cookie
        seed = self.cookies[name]
        return hmac.new(self.app.cfg.secret_key, f"csrf:{seed}".encode(), "sha256").hexdigest()

    def post(self, url: str, data: dict | None = None, csrf: bool = True, **kw) -> Resp:
        data = dict(data or {})
        if csrf and "csrf" not in data:
            data["csrf"] = self.csrf()
        return self.request("POST", url, data=data, **kw)

    # flows -----------------------------------------------------------------
    def email_signin(self, email: str, invite: str = "") -> Resp:
        r = self.post("/signin/email", {"email": email, "invite": invite})
        assert r.status == 303 and r.location == "/signin/check", r.text
        return r

    def follow_last_link(self) -> Resp:
        link = last_mail(self.app)["links"][0]
        path = urllib.parse.urlsplit(link)
        r = self.get(f"{path.path}?{path.query}")
        assert r.status == 200, r.text
        token = urllib.parse.parse_qs(path.query)["t"][0]
        return self.post("/signin/link", {"t": token})

    def onboard(self, name: str = "Maya R.", help_: list[str] | None = None) -> Resp:
        r = self.post("/welcome", {"q_display_name": name, "q_help": help_ or ["meetings"],
                                   "q_neighbourhood": "Seabright"})
        assert r.status == 303 and r.location == "/home", r.text
        return r


def last_mail(app: App) -> dict:
    mails = app.mailer.recent()
    assert mails, "no mail sent"
    return mails[0]


def mail_code(mail: dict) -> str:
    m = re.search(r"code on the sign-in page: (\d{3}) (\d{3})", mail["text"])
    assert m, mail["text"]
    return m.group(1) + m.group(2)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_config(tmp_path: Path, **over) -> Config:
    cfg = Config(mode="test", base_url="http://127.0.0.1:8817", data_dir=tmp_path / "var",
                 content_dir=SITE / "content", secret_key=b"k" * 32,
                 leaders=frozenset({LEADER}), email_from="Test <signin@example.com>")
    for k, v in over.items():
        setattr(cfg, k, v)
    cfg.check()
    return cfg


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def app(tmp_path, clock):
    return App(make_config(tmp_path), clock=clock)


@pytest.fixture
def leader(app):
    c = Client(app)
    c.email_signin(LEADER)
    r = c.follow_last_link()
    assert r.location == "/welcome"
    c.onboard("Alex H.")
    return c


def make_invite(leader: Client, channel: str = "Instagram", **fields) -> dict:
    data = {"channel": channel, "kind": "link", "max_uses": "", "expires_days": "30"}
    data.update(fields)
    r = leader.post("/leader/invites", data)
    assert r.status == 303, r.text
    invite_id = r.location.rsplit("/", 1)[1]
    state = leader.app.service.invite_by_id(invite_id)
    return state.invite
