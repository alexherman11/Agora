"""Serve the application experiment in its own world; no guest or model is started.
Never connect to the active Desk or replace an existing world's installed source.
"""

import argparse
import json
import os
from pathlib import Path

from application_packages import bundle, prepare

from agora3.gateway import Gateway
from agora3.server import serve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", type=Path, default=Path("worlds/application-demo"))
    parser.add_argument("--port", type=int, default=8871)
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    gateway = Gateway(args.world)
    prepare(gateway)
    releases = args.world / "releases"
    releases.mkdir(exist_ok=True)
    for name in ("notes", "documents"):
        (releases / f"{name}.agora-app.json").write_text(
            json.dumps(bundle(name), indent=2), encoding="utf-8"
        )
    if not args.serve:
        print(json.dumps({"prepared": str(args.world.resolve()), "replay": gateway.world.verify()}))
        return
    server, app = serve(args.world, args.port)
    ready = {
        "pid": os.getpid(),
        "port": server.server_address[1],
        "world": str(args.world.resolve()),
        "guest_started": False,
        "model_started": False,
    }
    (args.world / "application-ready.json").write_text(json.dumps(ready, indent=2))
    print(json.dumps(ready), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.bridge.close()
        if app.jeff:
            app.jeff.close()


if __name__ == "__main__":
    main()
