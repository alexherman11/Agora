"""Continue with Google: OpenID Connect authorization-code flow with PKCE.

The browser carries only `state` and `code`. The nonce, the PKCE verifier and
the invite the person arrived with stay on the server, keyed by a short-lived
cookie, so a callback from another browser (login CSRF) finds no flow.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import jwt_rs256
from .config import Config

CLOCK_SKEW = 300
FLOW_SECONDS = 600


class OIDCError(Exception):
    pass


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)  # 64 characters, inside RFC 7636's 43..128
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge.rstrip(b"=").decode("ascii")


def _post_form(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read(1_000_000))
    except urllib.error.HTTPError as exc:
        raise OIDCError(f"token endpoint said {exc.code}") from exc
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        raise OIDCError("token endpoint unreachable") from exc


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read(1_000_000))
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        raise OIDCError("keys unreachable") from exc


class Google:
    def __init__(self, cfg: Config, clock=time.time):
        self.cfg = cfg
        self.clock = clock
        self.redirect_uri = cfg.base_url + "/auth/google/callback"
        self._keys: dict[str, tuple[int, int]] = {}
        self._keys_at = 0.0
        self._lock = threading.Lock()

    def authorize_url(self, state: str, nonce: str, challenge: str) -> str:
        query = urllib.parse.urlencode({
            "response_type": "code",
            "client_id": self.cfg.google_client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        })
        return f"{self.cfg.google_auth_url}?{query}"

    def exchange(self, code: str, verifier: str) -> str:
        body = _post_form(self.cfg.google_token_url, {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.cfg.google_client_id,
            "client_secret": self.cfg.google_client_secret,
            "code_verifier": verifier,
        })
        token = body.get("id_token")
        if not isinstance(token, str):
            raise OIDCError("no id_token in the reply")
        return token

    def _load_keys(self, force: bool = False) -> dict[str, tuple[int, int]]:
        with self._lock:
            if force or not self._keys or self.clock() - self._keys_at > 3600:
                doc = _get_json(self.cfg.google_jwks_url)
                keys = {}
                for jwk in doc.get("keys", []):
                    if jwk.get("kid") and jwk.get("kty") == "RSA":
                        try:
                            keys[jwk["kid"]] = jwt_rs256.jwk_to_key(jwk)
                        except (jwt_rs256.TokenError, KeyError):
                            continue
                self._keys, self._keys_at = keys, self.clock()
            return self._keys

    def verify(self, id_token: str, nonce: str) -> dict:
        try:
            kid = jwt_rs256.decode_header(id_token).get("kid")
            keys = self._load_keys()
            if kid not in keys:  # Google rotates keys; fetch once more
                keys = self._load_keys(force=True)
            claims = jwt_rs256.verify(id_token, keys)
        except jwt_rs256.TokenError as exc:
            raise OIDCError(f"id token rejected: {exc}") from exc
        now = self.clock()
        if claims.get("iss") not in self.cfg.google_issuers:
            raise OIDCError("wrong issuer")
        aud = claims.get("aud")
        auds = aud if isinstance(aud, list) else [aud]
        if self.cfg.google_client_id not in auds:
            raise OIDCError("token is for another client")
        if len(auds) > 1 and claims.get("azp") != self.cfg.google_client_id:
            raise OIDCError("token is for another client")
        if "azp" in claims and claims["azp"] != self.cfg.google_client_id:
            raise OIDCError("token is for another client")
        exp, iat = claims.get("exp"), claims.get("iat")
        if not isinstance(exp, (int, float)) or exp < now - CLOCK_SKEW:
            raise OIDCError("token expired")
        if not isinstance(iat, (int, float)) or iat > now + CLOCK_SKEW:
            raise OIDCError("token from the future")
        if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
            raise OIDCError("nonce mismatch")
        if not isinstance(claims.get("sub"), str) or not claims["sub"]:
            raise OIDCError("no subject")
        if claims.get("email_verified") not in (True, "true"):
            raise OIDCError("email not verified")
        if not isinstance(claims.get("email"), str):
            raise OIDCError("no email")
        return claims
