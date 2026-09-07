"""Local operator entry point; never substitutes host execution for a missing guest."""

import argparse
import json
import threading
from pathlib import Path

from agora3 import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agora3", description="Agora native world and Linux guest."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--world", type=Path, default=Path("worlds/dev"))
    commands = parser.add_subparsers(dest="command")
    server_parser = commands.add_parser("serve", help="Start the local world and editable shell.")
    server_parser.add_argument("--port", type=int, default=8790)
    commands.add_parser("verify", help="Compare object cache with journal replay.")
    commands.add_parser("rebuild", help="Rebuild the cache without executing code.")
    commands.add_parser("stop", help="Revoke development authority and stop the dedicated VM.")
    commands.add_parser("guest-status", help="Inspect the configured Linux guest.")
    args = parser.parse_args()
    if args.command == "serve":
        from agora3.server import serve

        server, app = serve(args.world, args.port)
        threading.Thread(target=app.connect_guest, daemon=True, name="agora-native-bridge").start()
        print(
            f"Agora is running. Open http://127.0.0.1:{args.port}/#{app.gateway.keep['operator']}",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            app.stop()
        finally:
            app.bridge.close()
            if app.jeff:
                app.jeff.close()
            server.server_close()
    elif args.command in {"verify", "rebuild"}:
        from agora3.world import World

        print(json.dumps(getattr(World(args.world), args.command)(), indent=2))
    elif args.command in {"stop", "guest-status"}:
        from agora3.gateway import Gateway

        gateway = Gateway(args.world)
        if args.command == "stop":
            gateway.revoke()
            print(json.dumps(gateway.guest.stop(), indent=2))
        else:
            print(json.dumps(gateway.guest.status(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
