"""Run the entry service: `python -m agora_entry` from the site folder.

Test mode (the default) listens on 127.0.0.1:8817, writes email to
var/outbox/, and, without Google keys, runs the Google stand-in on 8818.

`python -m agora_entry signin-link <email>` prints a one-time sign-in link for
a leader (SITE_LEADERS) or an existing member, for when there is no SMTP yet.
It reads the same settings and store as the server, so run it where the
server runs. The link works once, for 15 minutes, like an emailed one.
"""

from __future__ import annotations

import socketserver
import sys
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from . import config
from .web import App


class ThreadingServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        # Never log query strings: sign-in links carry their token there.
        line = (self.requestline or "").split("?", 1)[0]
        sys.stderr.write(f"{self.log_date_time_string()} {line} {args[1] if len(args) > 1 else ''}\n")


def signin_link(argv: list[str], env: dict | None = None, out=None, err=None, dotenv=None) -> int:
    """`signin-link <email>`: print the link on stdout. -> exit status."""
    out, err = out or sys.stdout, err or sys.stderr
    if len(argv) != 1:
        print("usage: python -m agora_entry signin-link <email>", file=err)
        return 2
    from .db import Store
    from .questions import load as load_questions
    from .service import Service
    cfg = config.from_env(env, dotenv=dotenv)
    service = Service(cfg, Store(cfg.data_dir / "entry.sqlite3"),
                      load_questions(cfg.content_dir / "questions.json"))
    try:
        link = service.mint_signin_link(argv[0])
    except ValueError as exc:
        print(f"no link: {exc}", file=err)
        return 1
    print(link, file=out)
    print(f"works once, for the next {cfg.link_minutes} minutes", file=err)
    return 0


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "signin-link":
        sys.exit(signin_link(argv[1:]))
    if argv:
        sys.exit(f"unknown command {argv[0]!r}; try: signin-link <email>")
    cfg = config.from_env()
    if cfg.google_mode == "fake":
        from .fake_google import StandIn, serve_in_thread
        stand_in = StandIn(cfg.google_client_id, cfg.google_client_secret,
                           cfg.base_url + "/auth/google/callback", cfg.google_issuers[0])
        serve_in_thread(stand_in, cfg.fake_google_port)
    app = App(cfg)
    server = make_server(cfg.host, cfg.port, app, server_class=ThreadingServer,
                         handler_class=QuietHandler)
    print(f"entry service, {cfg.mode} mode, on {cfg.base_url}"
          f" (google: {cfg.google_mode}, email: {cfg.email_mode},"
          f" per-IP limits: {'on' if cfg.ip_limits else 'off'})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
