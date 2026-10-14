"""Publish the authored lens/style through native operations, using existing IDs."""

import argparse
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--actor", default="codex")
    parser.add_argument("--port", type=int, default=8794)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    ids = json.loads(args.manifest.read_text(encoding="utf-8"))

    def act(command):
        body = json.dumps({"session": args.session, "as": args.actor,
                           "line": command, "whole": True}).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{args.port}/api/do", body,
            {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
        text = result.get("text", "")
        if result.get("error") or any(
            line.startswith(("ERR ", "MISS ", "stopped")) for line in text.splitlines()
        ):
            raise RuntimeError(text or result["error"])
        return text

    for key, filename in (("style", "conversation.style"), ("lens", "conversation.lens")):
        source = Path(__file__).with_name(filename).read_text(encoding="utf-8")
        source = source.replace("FEED_ID", ids["feed"])
        act(f"read {ids[key]} :3")
        print(act(f"do rewrite {ids[key]} text=" + json.dumps(source, ensure_ascii=False)))


if __name__ == "__main__":
    main()
