"""Settings for the entry service.

Everything comes from the process environment, then from a `.env` file that
Alex writes himself (never from this repository). Test mode needs no keys at
all: email goes to a local outbox and Google is played by a local stand-in.
"""

from __future__ import annotations

import ipaddress
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

SITE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")


def load_dotenv(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines. Comments and blank lines are skipped."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key] = value
    return values


def is_loopback_host(host: str) -> bool:
    if host in ("localhost",) or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


@dataclass
class Config:
    mode: str  # "test" or "live"
    base_url: str
    host: str = "127.0.0.1"
    port: int = 8817
    data_dir: Path = SITE_DIR / "var"
    content_dir: Path = SITE_DIR / "content"
    secret_key: bytes = b""

    google_mode: str = "off"  # "off", "real" or "fake"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_auth_url: str = GOOGLE_AUTH_URL
    google_token_url: str = GOOGLE_TOKEN_URL
    google_jwks_url: str = GOOGLE_JWKS_URL
    google_issuers: tuple[str, ...] = GOOGLE_ISSUERS
    fake_google_port: int = 0

    email_mode: str = "file"  # "file" or "smtp"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""

    leaders: frozenset[str] = field(default_factory=frozenset)
    proxy_ip_header: str = ""  # e.g. "CF-Connecting-IP" behind Cloudflare
    kernel_secret: str = ""

    session_days: int = 90
    session_idle_days: int = 30
    link_minutes: int = 15

    @property
    def secure_cookies(self) -> bool:
        return self.base_url.startswith("https://")

    @property
    def base_origin(self) -> str:
        parts = urlsplit(self.base_url)
        return f"{parts.scheme}://{parts.netloc}"

    @property
    def is_test(self) -> bool:
        return self.mode == "test"

    def check(self) -> None:
        """Refuse settings that would be unsafe. Raises ValueError."""
        if self.mode not in ("test", "live"):
            raise ValueError("SITE_MODE must be 'test' or 'live'")
        if len(self.secret_key) < 32:
            raise ValueError("secret key is missing or too short")
        if self.mode == "test":
            if not is_loopback_host(self.host):
                raise ValueError("test mode only listens on loopback")
            if self.email_mode != "file":
                raise ValueError("test mode writes email to the local outbox only")
        else:
            if not self.base_url.startswith("https://"):
                raise ValueError("live mode needs an https SITE_BASE_URL")
            if self.google_mode == "fake":
                raise ValueError("the Google stand-in only runs in test mode")
            if self.email_mode != "smtp" or not (self.smtp_host and self.email_from):
                raise ValueError("live mode needs EMAIL_SMTP_HOST and EMAIL_FROM")


def _secret_from_file(data_dir: Path) -> bytes:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "secret.key"
    if path.is_file():
        return bytes.fromhex(path.read_text(encoding="ascii").strip())
    key = secrets.token_bytes(32)
    path.write_text(key.hex(), encoding="ascii")
    return key


def from_env(env: dict[str, str] | None = None, dotenv: Path | None = None) -> Config:
    merged: dict[str, str] = {}
    merged.update(load_dotenv(dotenv if dotenv is not None else SITE_DIR / ".env"))
    merged.update(env if env is not None else os.environ)
    get = lambda k, d="": merged.get(k, d).strip()  # noqa: E731

    mode = get("SITE_MODE", "test")
    host = get("SITE_HOST", "127.0.0.1")
    port = int(get("SITE_PORT", "8817"))
    base_url = get("SITE_BASE_URL", f"http://{host}:{port}").rstrip("/")
    data_dir = Path(get("SITE_DATA_DIR", str(SITE_DIR / "var")))

    secret_hex = get("SITE_SECRET_KEY")
    secret = bytes.fromhex(secret_hex) if secret_hex else _secret_from_file(data_dir)

    cfg = Config(mode=mode, base_url=base_url, host=host, port=port,
                 data_dir=data_dir, secret_key=secret)

    cid, csecret = get("GOOGLE_CLIENT_ID"), get("GOOGLE_CLIENT_SECRET")
    if cid and csecret:
        cfg.google_mode = "real"
        cfg.google_client_id, cfg.google_client_secret = cid, csecret
    elif mode == "test" and get("GOOGLE_STAND_IN", "on") != "off":
        cfg.google_mode = "fake"
        cfg.fake_google_port = port + 1
        stand_in = f"http://127.0.0.1:{cfg.fake_google_port}"
        cfg.google_client_id, cfg.google_client_secret = "stand-in-client", "stand-in-secret"
        cfg.google_auth_url = stand_in + "/authorize"
        cfg.google_token_url = stand_in + "/token"
        cfg.google_jwks_url = stand_in + "/certs"
        cfg.google_issuers = (stand_in,)

    if mode == "live":
        cfg.email_mode = "smtp"
        cfg.smtp_host = get("EMAIL_SMTP_HOST")
        cfg.smtp_port = int(get("EMAIL_SMTP_PORT", "587"))
        cfg.smtp_user = get("EMAIL_SMTP_USER")
        cfg.smtp_password = get("EMAIL_SMTP_PASSWORD")
    cfg.email_from = get("EMAIL_FROM", "Seabright Neighbours <signin@localhost>")

    cfg.leaders = frozenset(
        e.strip().lower() for e in get("SITE_LEADERS").split(",") if e.strip()
    )
    if mode == "test" and not cfg.leaders:
        # A pretend leader so test mode can make invites. example.com never
        # receives mail; the outbox is a local file anyway.
        cfg.leaders = frozenset({"leader@example.com"})
    cfg.proxy_ip_header = get("SITE_PROXY_IP_HEADER")
    cfg.kernel_secret = get("KERNEL_SHARED_SECRET")
    cfg.check()
    return cfg
