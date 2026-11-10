"""Source-before-world gate for an author's exact dependency manifest.

This proves committed bytes, not that a running process has loaded them. The
activation owner must verify runtime identity before installing dependent views.
"""

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path


class SourceNotIntegrated(RuntimeError):
    pass


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)


def inspect_sources(root, files):
    root = Path(root).resolve()
    main = _git(root, "rev-parse", "--verify", "refs/heads/main^{commit}")
    head = _git(root, "rev-parse", "HEAD")
    revision = main.stdout.decode().strip() if main.returncode == 0 else ""
    problems, checks = [], []
    if not revision or head.returncode or head.stdout.decode().strip() != revision:
        problems.append("The live checkout must be on the committed main revision.")
    if not isinstance(files, dict) or not files:
        raise SourceNotIntegrated(
            "Supply the complete nonempty path-to-SHA256 dependency manifest."
        )
    for name, expected in sorted(files.items()):
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not (root / path).resolve().is_relative_to(root)
        ):
            raise SourceNotIntegrated(f"Dependency escapes the checkout: {name}")
        if (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(c not in "0123456789abcdef" for c in expected)
        ):
            raise SourceNotIntegrated(f"Expected an exact lowercase SHA256 for {name}")
        try:
            working = hashlib.sha256((root / path).read_bytes()).hexdigest()
        except OSError:
            working = None
        blob = _git(root, "show", f"{revision}:{path.as_posix()}") if revision else None
        committed = (
            hashlib.sha256(blob.stdout).hexdigest() if blob and blob.returncode == 0 else None
        )
        ok = working == expected and committed == expected
        checks.append(
            dict(
                path=path.as_posix(),
                expected=expected,
                working=working,
                committed=committed,
                ok=ok,
            )
        )
        if not ok:
            problems.append(
                f"{path.as_posix()}: reviewed bytes are missing or differ from committed main."
            )
    # A concurrent landing is not the revision we just checked.
    final = _git(root, "rev-parse", "HEAD", "refs/heads/main")
    if final.returncode or final.stdout.decode().splitlines() != [revision, revision]:
        problems.append(
            "Main changed during preflight; inspect the new revision before installation."
        )
    return dict(
        ok=not problems,
        revision=revision,
        files=checks,
        problems=problems,
        runtime_verified=False,
    )


def require_sources(root, files):
    receipt = inspect_sources(root, files)
    if not receipt["ok"]:
        raise SourceNotIntegrated(
            "Source must land before dependent world installation: "
            + "; ".join(receipt["problems"])
        )
    return receipt


def runtime_sources(root):
    """Capture tracked source bytes before backend imports, never session data.

    A newly committed dependency absent at startup requires normal activation.
    This is a startup observation, not a claim about arbitrary external programs.
    """
    root = Path(root).resolve()
    names = _git(root, "ls-files", "-z")
    if names.returncode:
        return {}
    result = {}
    for name in names.stdout.decode("utf-8").split("\0"):
        if Path(name).suffix not in {".py", ".js", ".html", ".css", ".style", ".lens"}:
            continue
        path = root / name
        if not path.resolve().is_relative_to(root):
            continue
        try:
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue  # An unavailable dependency cannot later pass its exact check.
    return result


def require_activation(root, manifest, runtime_code, startup_sources):
    """Mandatory before a source-dependent installation command is dispatched."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("revision"), str):
        raise SourceNotIntegrated("An exact source revision and files manifest are required.")
    receipt = require_sources(root, manifest.get("files"))
    runtime = _git(root, "rev-parse", "--verify", f"{runtime_code}^{{commit}}")
    actual = runtime.stdout.decode().strip() if runtime.returncode == 0 else ""
    if manifest["revision"] != receipt["revision"] or actual != receipt["revision"]:
        raise SourceNotIntegrated(
            "The answering backend has not activated the reviewed main revision."
        )
    for item in receipt["files"]:
        if startup_sources.get(item["path"]) != item["expected"]:
            raise SourceNotIntegrated(
                f"{item['path']}: reviewed bytes were not observed at backend startup."
            )
    return {**receipt, "runtime_verified": True, "runtime_revision": actual}


def deploy_line(root, files, line, *, url, world, actor):
    """One admitted normal world command; no retries after an uncertain response.

    /api/deploy requires the gate on the answering backend. An older backend
    rejects the unknown route before dispatch instead of ignoring extra fields.
    Ordinary seen/revision fences and command authorization are unchanged.
    """
    source = require_sources(root, files)
    body = {
        "session": world,
        "as": actor,
        "line": line,
        "whole": True,
        "source_dependencies": {"revision": source["revision"], "files": files},
    }
    request = urllib.request.Request(
        url.rstrip("/") + "/api/deploy",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        answer = json.load(response)
    if not answer.get("source_verified"):
        raise SourceNotIntegrated(
            "Installation was refused or unverified; inspect its receipt before any retry: "
            + str(answer.get("error") or "missing verification")
        )
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest", type=Path, help="JSON object containing a files path-to-SHA256 map"
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    try:
        receipt = inspect_sources(args.root, json.loads(args.manifest.read_text())["files"])
    except (OSError, ValueError, KeyError, SourceNotIntegrated) as exc:
        receipt = dict(ok=False, problems=[str(exc)], runtime_verified=False)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
