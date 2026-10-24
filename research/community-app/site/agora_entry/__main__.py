"""Run the entry service: `python -m agora_entry` from the site folder.

Test mode (the default) listens on 127.0.0.1:8817, writes email to
var/outbox/, and, without Google keys, runs the Google stand-in on 8818.
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


def main() -> None:
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
          f" (google: {cfg.google_mode}, email: {cfg.email_mode})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
