"""RS256 JSON Web Tokens: verify (for Google's ID tokens) and sign (for the stand-in).

Standard library only. Verification follows RFC 8017 section 8.2.2: rebuild
the whole expected PKCS#1 v1.5 encoding and compare it byte for byte, never
parse the decrypted block, so the old "lenient parser" forgeries cannot apply.
The ID token also arrives straight from Google's token endpoint over TLS,
which OpenID Connect Core 3.1.3.7 already accepts as proof of origin; the
signature check is a second wall, not the only one.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets

# DER prefix of DigestInfo for SHA-256 (RFC 8017, section 9.2, note 1).
_SHA256_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


class TokenError(Exception):
    pass


def b64url_decode(text: str) -> bytes:
    if not isinstance(text, str) or any(c in text for c in "+/= \n"):
        raise TokenError("not base64url")
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise TokenError("not base64url") from exc


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _int(data: bytes) -> int:
    return int.from_bytes(data, "big")


def jwk_to_key(jwk: dict) -> tuple[int, int]:
    if jwk.get("kty") != "RSA":
        raise TokenError("key is not RSA")
    n, e = _int(b64url_decode(jwk["n"])), _int(b64url_decode(jwk["e"]))
    if n.bit_length() < 2048:
        raise TokenError("key too small")
    return n, e


def _expected_encoding(signing_input: bytes, k: int) -> bytes:
    t = _SHA256_PREFIX + hashlib.sha256(signing_input).digest()
    if k < len(t) + 11:
        raise TokenError("key too small")
    return b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t


def rsa_verify(signing_input: bytes, signature: bytes, n: int, e: int) -> bool:
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    s = _int(signature)
    if s >= n:
        return False
    em = pow(s, e, n).to_bytes(k, "big")
    return hmac.compare_digest(em, _expected_encoding(signing_input, k))


def decode_header(token: str) -> dict:
    parts = token.split(".") if isinstance(token, str) else []
    if len(parts) != 3:
        raise TokenError("not a JWT")
    try:
        header = json.loads(b64url_decode(parts[0]))
    except ValueError as exc:
        raise TokenError("bad header") from exc
    if not isinstance(header, dict):
        raise TokenError("bad header")
    return header


def verify(token: str, keys: dict[str, tuple[int, int]]) -> dict:
    """Check the signature with the key named by `kid`. Returns the claims."""
    header = decode_header(token)
    if header.get("alg") != "RS256":
        raise TokenError("only RS256 is accepted")
    kid = header.get("kid")
    if kid not in keys:
        raise TokenError("unknown key id")
    head_b64, body_b64, sig_b64 = token.split(".")
    n, e = keys[kid]
    if not rsa_verify(f"{head_b64}.{body_b64}".encode("ascii"), b64url_decode(sig_b64), n, e):
        raise TokenError("bad signature")
    try:
        claims = json.loads(b64url_decode(body_b64))
    except ValueError as exc:
        raise TokenError("bad claims") from exc
    if not isinstance(claims, dict):
        raise TokenError("bad claims")
    return claims


# --- signing, for the local Google stand-in and the tests only -------------

def _probable_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(40):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


_SMALL_PRIMES = [p for p in range(3, 2000, 2) if all(p % q for q in range(3, int(p ** 0.5) + 1, 2))]


def _prime(bits: int) -> int:
    while True:
        c = secrets.randbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if _probable_prime(c):
            return c


def generate_key(bits: int = 2048) -> dict:
    e = 65537
    while True:
        p, q = _prime(bits // 2), _prime(bits // 2)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e and (p * q).bit_length() == bits:
            return {"n": p * q, "e": e, "d": pow(e, -1, phi)}


def public_jwk(key: dict, kid: str) -> dict:
    k = (key["n"].bit_length() + 7) // 8
    return {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": kid,
            "n": b64url_encode(key["n"].to_bytes(k, "big")),
            "e": b64url_encode(key["e"].to_bytes(3, "big"))}


def sign(claims: dict, key: dict, kid: str, alg: str = "RS256") -> str:
    head = b64url_encode(json.dumps({"alg": alg, "kid": kid, "typ": "JWT"}).encode())
    body = b64url_encode(json.dumps(claims).encode())
    k = (key["n"].bit_length() + 7) // 8
    em = _expected_encoding(f"{head}.{body}".encode("ascii"), k)
    sig = pow(_int(em), key["d"], key["n"]).to_bytes(k, "big")
    return f"{head}.{body}.{b64url_encode(sig)}"
