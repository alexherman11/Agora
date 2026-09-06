"""Local browser sessions: host/origin checks and mutation tokens.
Never: never trusts an actor supplied by the browser or grants extension code a session."""

import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware


def install(app):
    token = secrets.token_urlsafe(32)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"])

    @app.middleware("http")
    async def boundary(request, call_next):
        origin = request.headers.get("origin")
        own = str(request.base_url).rstrip("/")
        if origin is not None and origin != own:
            return JSONResponse({"error": "foreign origin refused"}, 403)
        public = request.url.path in ("/", "/session", "/app.js", "/style.css", "/components.js")
        if not public and not secrets.compare_digest(
            request.cookies.get("agora_session", ""), token
        ):
            return JSONResponse({"error": "open the local Agora page to establish a session"}, 401)
        if request.method == "POST":
            if not secrets.compare_digest(request.headers.get("x-agora-session", ""), token):
                return JSONResponse({"error": "mutation requires the local session token"}, 403)
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return JSONResponse({"error": "expected application/json"}, 415)
            if len(await request.body()) > 10 * 1024 * 1024:
                return JSONResponse({"error": "request exceeds 10 MiB"}, 413)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/session")
    async def session():
        response = JSONResponse({"token": token})
        response.set_cookie("agora_session", token, httponly=True, samesite="strict")
        return response
