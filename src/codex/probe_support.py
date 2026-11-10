"""Isolated mock-probe artifacts; never load the signed-in CODEX_HOME."""

import argparse
import json
import os
import shutil
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent


@contextmanager
def probe_directory():
    root = HERE.parents[1] / "local/codex-residents"
    path = root / ("pin-probe-" + uuid.uuid4().hex)
    # tempfile's owner-only Windows ACL prevents sandbox children writing here.
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        # app-server releases sqlite handles just after transport shutdown.
        for attempt in range(10):
            try:
                shutil.rmtree(path)
                break
            except OSError:
                if attempt == 9:
                    # Keep failed scratch evidence; never hide a probe failure.
                    print(f"Scratch cleanup deferred: {path}")
                else:
                    time.sleep(0.1)


def options(kind):
    if not __debug__:
        raise RuntimeError("Probe assertions must be enabled")
    parser = argparse.ArgumentParser(description="Empty-profile, loopback-only runtime probe")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="gpt-6-astra" if kind == "resident" else "gpt-6.1-sol")
    args = parser.parse_args()
    from runtime_pin import CATALOGS, INVENTORIES, LOCKS

    reserved = {HERE / name for name in LOCKS + CATALOGS + INVENTORIES}
    if args.output.resolve() in {path.resolve() for path in reserved}:
        parser.error("Probe output must not overwrite trusted runtime files")
    if args.binary is None:
        from runtime_pin import ensure_runtime

        args.binary = Path(ensure_runtime()["binary"])
    return args


def isolated_environment(directory, profile):
    """Child-only home redirects; no persistent profile or account changes."""
    env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("CODEX_") and k not in ("OPENAI_API_KEY", "OPENAI_BASE_URL")
    }
    env.update(
        CODEX_HOME=str(profile), HOME=str(profile), USERPROFILE=str(profile),
        APPDATA=str(profile), LOCALAPPDATA=str(profile),
        TMP=str(directory), TEMP=str(directory), TMPDIR=str(directory),
    )
    env.pop("HOMEDRIVE", None)
    env.pop("HOMEPATH", None)
    return env


def empty_profile(directory):
    profile = Path(directory) / "empty-home"
    profile.mkdir()
    # The SDK inherits its parent env. Remove presence-only internal flags and
    # API-key overrides for mock probes. This changes only the probe process.
    env = isolated_environment(directory, profile)
    os.environ.clear()
    os.environ.update(env)
    return profile


def fixture_mcp(directory):
    """Use the real advertised tool schema, but replace all Desk execution."""
    import sys

    lab = HERE.parent / "text-desk/notation"
    server = Path(directory) / "fixture_desk.py"
    server.write_text(
        "import sys,json\n"
        f"sys.path.insert(0,{str(lab)!r})\n"
        "import desk_mcp\n"
        "desk_mcp.run_desk=lambda args: ('PIN_FIXTURE_DESK_OK',False)\n"
        "for line in sys.stdin:\n"
        "    desk_mcp.handle(json.loads(line))\n",
        encoding="utf-8",
    )
    mcp = Path(directory) / "mcp.json"
    mcp.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "desk": {
                        "command": sys.executable,
                        "args": [str(server)],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return mcp
