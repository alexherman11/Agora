"""Fail-closed runtime update gate shared by both Codex adapters.

Only this module writes the two runtime locks. Candidate processes see empty
profiles and loopback mock inference, never the sign-in profile. Locks, receipts
and previous versions are committed under one interprocess lock. An interrupted
two-file publication is rolled back before either adapter may start.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

HERE = Path(__file__).resolve().parent
LOCKS = ("runtime-lock.json", "worker-runtime-lock.json")
CATALOGS = ("model-catalog.json", "worker-model-catalog.json")
INVENTORIES = ("runtime-inventory.json", "worker-runtime-inventory.json")


class PinRefused(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PinRefused("The local house door redirected the runtime record")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def catalog_matches(path, expected):
    raw = Path(path).read_bytes()
    # These old locks pin CRLF; allow only Git's exact LF checkout conversion.
    return expected in {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest(),
    }


def tools(inventory):
    """Compare whole tool declarations, including schemas and descriptions."""
    found = list(inventory.get("tools") or [])
    for item in inventory.get("input", inventory.get("messages", [])) or []:
        found.extend(item.get("tools") or [])
    return sorted(found, key=lambda t: json.dumps(t, sort_keys=True))


def version_key(value):
    match = re.fullmatch(r"codex-cli (\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", value.strip())
    if not match:
        raise PinRefused("Runtime did not print a recognized codex-cli version")
    major, minor, patch = map(int, match.group(1, 2, 3))
    suffix = match.group(4)
    # Semver prerelease components: numeric before text, release after prerelease.
    pre = tuple((0, int(x)) if x.isdigit() else (1, x) for x in (suffix or "").split("."))
    return (major, minor, patch, suffix is None, pre)


def permit_version(old, new, same_binary=False):
    before, after = version_key(old), version_key(new)
    if before[0] != after[0]:
        raise PinRefused(f"Major version changed: {old} -> {new}")
    if after < before or (after == before and not same_binary):
        raise PinRefused(f"Not a forward patch/minor update: {old} -> {new}")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(path.name + "." + uuid.uuid4().hex)
    try:
        with stage.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)


@contextmanager
def mutex(root):
    from worker_lease import worker_leases

    # Share the house's process-held lease implementation (also released on kill).
    try:
        with worker_leases([root / "checker.lock"], timeout=300):
            yield
    except RuntimeError as error:
        raise PinRefused(str(error)) from error


class WorldRecord:
    """Local house API; inert identity, idempotent gestures, no resident calls."""

    def __init__(self, url=None):
        self.url = url if url is not None else (os.environ.get("DESKD") or "http://127.0.0.1:8794")

    def act(self, line, gesture=None):
        parsed = urlparse(self.url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in ("127.0.0.1", "localhost")
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise PinRefused("Runtime records require the local house door")
        body = json.dumps(
            {
                "session": "frontier",
                "as": "runtime-pins",
                "line": line,
                "whole": True,
                **({"gesture": gesture} if gesture else {}),
            }
        ).encode()
        # Never send world records through an inherited proxy or an HTTP redirect.
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open(
            Request(self.url.rstrip("/") + "/api/do", body, {"Content-Type": "application/json"}),
            timeout=30,
        ) as stream:
            reply = json.load(stream)
        text = reply.get("text") or ""
        if reply.get("error") or any(
            s.startswith(("ERR ", "MISS ", "stopped")) for s in text.splitlines()
        ):
            raise PinRefused("The house refused the runtime record")
        return text

    def __call__(self, kind, key, record):
        self.act("look")
        if kind == "notice":
            target = self.target("notifications", "chat")
            self.act(f"read {target} tail=1")
            change = (
                f" ({record['old_version']} -> {record.get('new_version', 'unverified candidate')})"
                if record.get("old_version")
                else ""
            )
            line = (
                "Codex runtime check refused"
                + change
                + ": "
                + record["reason"]
                + ". The previous pin is unchanged. "
                + "JEFF will review the failed check before agents restart."
            )
            self.act(
                f"do append {target} line=" + quote(line) + " to=nobody",
                "pin-notice-" + key,
            )
        else:
            target = self.target("runtime-pins", "note")
            self.act(f"read {target}")
            self.act(
                f"do append {target} line=" + quote(json.dumps(record, ensure_ascii=False)),
                "pin-record-" + key,
            )

    def target(self, role, kind):
        found = self.act("find role=" + role)
        matches = re.findall(r"(?m)^\s+(a\d+) " + kind + r"\s", found)
        if len(matches) != 1:
            raise PinRefused(f"The house needs exactly one {kind} with role={role}")
        return matches[0]


def quote(value):
    # Desk quotation, not shell quotation (protect its variable expansion too).
    return json.dumps(value, ensure_ascii=False).replace("$", r"\$")


def authenticode(binary):
    """Ask Windows about the file; never execute the candidate to identify it."""
    if os.name != "nt":
        raise PinRefused("Automatic runtime approval requires Windows Authenticode")
    script = (
        "$ErrorActionPreference='Stop'; "
        "$s=Get-AuthenticodeSignature -LiteralPath $env:AGORA_PIN_CANDIDATE; "
        "@{status=$s.Status.ToString(); "
        "publisher=if($s.SignerCertificate){"
        "$s.SignerCertificate.GetNameInfo('SimpleName',$false)}else{''}; "
        "thumbprint=if($s.SignerCertificate){$s.SignerCertificate.Thumbprint}else{''}} "
        "| ConvertTo-Json -Compress"
    )
    command = str(
        Path(os.environ.get("SystemRoot", r"C:\Windows"))
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    result = subprocess.run(
        [command, "-NoProfile", "-NonInteractive", "-EncodedCommand",
         base64.b64encode(script.encode("utf-16-le")).decode("ascii")],
        env={**os.environ, "AGORA_PIN_CANDIDATE": str(binary)},
        capture_output=True, text=True, timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        raise PinRefused("Windows could not verify the candidate publisher signature")
    return json.loads(result.stdout)


class Checker:
    def __init__(self, here=HERE, state=None, installs=None, record=None, probe=None,
                 version=None, signature=None):
        self.here = Path(here)
        self.state = (
            Path(state) if state else self.here.parents[1] / "local/codex-residents/pin-checker"
        )
        self.installs = (
            Path(installs)
            if installs
            else (
                Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
                / "OpenAI/Codex/bin"
            )
        )
        self.record = record if record is not None else WorldRecord()
        self.probe = probe or self.probe_runtime
        self.version = version or self.printed_version
        self.signature = signature or authenticode

    def installed_source(self, candidate, expected):
        """Retained pins must still have an identical updater-installed source."""
        root = self.installs.resolve()
        candidate = candidate.resolve()
        if candidate.name.lower() == "codex.exe" and candidate.parent.parent == root:
            return candidate
        for path in self.installs.glob("*/codex.exe"):
            if path.resolve().parent.parent == root and path.is_file() and digest(path) == expected:
                return path
        raise PinRefused("Candidate is outside Codex's own bin folder; no identical install exists")

    def read_locks(self):
        locks = [json.loads((self.here / name).read_text(encoding="utf-8")) for name in LOCKS]
        for field in ("binary", "binary_sha256", "version", "sdk"):
            if locks[0][field] != locks[1][field]:
                raise PinRefused("Resident and worker locks disagree; manual review needed")
        for lock, name in zip(locks, CATALOGS, strict=True):
            if not catalog_matches(self.here / name, lock["catalog_sha256"]):
                raise PinRefused(f"Pinned catalog changed: {name}")
        return locks

    def recover(self):
        journal = self.state / "transaction.json"
        if journal.exists():
            tx = json.loads(journal.read_text(encoding="utf-8"))
            # A complete publication remains committed. Otherwise restore BOTH.
            try:
                complete = all(
                    json.loads((self.here / n).read_text(encoding="utf-8")) == v
                    for n, v in zip(LOCKS, tx["new"], strict=True)
                )
            except (OSError, ValueError):
                complete = False
            if not complete:
                for name, value in zip(LOCKS, tx["old"], strict=True):
                    atomic_json(self.here / name, value)
            journal.unlink()

    def flush_records(self):
        for path in self.state.glob("pending-*.json"):
            report = json.loads(path.read_text(encoding="utf-8"))
            if path.name.startswith("pending-notice-"):
                key = path.stem.removeprefix("pending-notice-")
                kind = "notice"
            else:
                key, kind = report["receipt"] + "-pub", "published"
            try:
                self.record(kind, key, report)
            except Exception as error:
                report["record_error"] = f"{type(error).__name__}: {error}"
                atomic_json(path, report)
                continue
            if kind == "notice":
                atomic_json(self.state / ("notice-" + key + ".json"), report)
            path.unlink()

    def gate_results(self, results):
        if not results.get("passed"):
            raise PinRefused("Candidate probes did not all pass")
        expected = {
            ("resident", "gpt-6-astra"),
            ("worker", "gpt-6.1-sol"),
            ("worker", "gpt-6-astra"),
        }
        runs = results.get("runs", [])
        if len(runs) != 3 or {(r["kind"], r["model"]) for r in runs} != expected:
            raise PinRefused("Candidate probe matrix is incomplete")
        verified = []
        for run in runs:
            kind, model = run["kind"], run["model"]
            actual = run["inventory"]
            if actual.get("model") != model:
                raise PinRefused(f"{kind} probe model was substituted")
            baseline = json.loads(
                (self.here / INVENTORIES[0 if kind == "resident" else 1]).read_text(
                    encoding="utf-8"
                )
            )
            if tools(actual) != tools(baseline):
                atomic_json(self.state / "changed-tool-inventory.json", actual)
                raise PinRefused(f"{kind} tool declarations changed for {model}")
            if kind == "resident":
                if actual.get("instructions") or any(
                    i.get("role") in ("system", "developer") for i in actual.get("messages", [])
                ):
                    raise PinRefused("Resident candidate injected instructions")
                if not any(
                    e.get("type") == "result"
                    and not e.get("is_error")
                    and e.get("result") == "> look\n> rest"
                    for e in actual.get("reply", [])
                ):
                    raise PinRefused("Resident protocol did not reach the house boundary")
            verified.append(
                {
                    "kind": kind,
                    "model": model,
                    "tools_match": True,
                    "passed": True,
                    "inventory_sha256": hashlib.sha256(
                        json.dumps(actual, sort_keys=True).encode()
                    ).hexdigest(),
                }
            )
        return {"passed": True, "empty_codex_home": True, "mock_inference": True, "runs": verified}

    def candidate(self, pinned):
        candidates = []
        if self.installs.is_dir():
            for path in self.installs.glob("*/codex.exe"):
                if path.is_file() and path.resolve().parent.parent == self.installs.resolve():
                    candidates.append(path)
        if not candidates:
            raise PinRefused("Pinned binary is missing or changed; no installed candidate exists")
        path = max(candidates, key=lambda p: (p.stat().st_mtime_ns, str(p)))
        if path.resolve() == Path(pinned["binary"]).resolve():
            raise PinRefused("Pinned binary hash is corrupted; it cannot approve itself")
        return path

    def check(self, recheck=False, rollback=None):
        with mutex(self.state):
            key = "unreadable-lock"
            change = {}
            try:
                self.recover()
                self.flush_records()
                old = self.read_locks()
                pinned = old[0]
                change = {"old_version": pinned["version"], "old_hash": pinned["binary_sha256"]}
                key = hashlib.sha256(json.dumps(pinned, sort_keys=True).encode()).hexdigest()
                valid = (
                    Path(pinned["binary"]).is_file()
                    and digest(pinned["binary"]) == pinned["binary_sha256"]
                )
                if valid and not recheck and rollback is None:
                    return pinned
                inputs = {name: digest(self.here / name) for name in CATALOGS + INVENTORIES}
                if rollback is not None:
                    # Only previous checker snapshots, never caller-supplied locks.
                    if not re.fullmatch(r"[0-9a-f]{32}", rollback):
                        raise PinRefused("Rollback must name a checker history receipt")
                    previous = json.loads(
                        (self.state / "history" / rollback / "previous.json").read_text()
                    )
                    candidate = Path(previous[0]["binary"])
                    if not candidate.is_file() or digest(candidate) != previous[0]["binary_sha256"]:
                        raise PinRefused("Previous runtime is missing or corrupted")
                else:
                    candidate = Path(pinned["binary"]) if valid else self.candidate(pinned)
                candidate_hash = digest(candidate)
                candidate = self.installed_source(candidate, candidate_hash)
                change["new_hash"] = candidate_hash
                key = hashlib.sha256(
                    (pinned["binary_sha256"] + candidate_hash).encode()
                ).hexdigest()
                # Copy first, check the exact retained bytes, then start probes.
                retained = self.state / "runtime" / candidate_hash / "codex.exe"
                retained.parent.mkdir(parents=True, exist_ok=True)
                if not retained.exists():
                    stage = retained.with_name(uuid.uuid4().hex + ".exe")
                    shutil.copyfile(candidate, stage)
                    if digest(stage) != candidate_hash:
                        raise PinRefused("Candidate changed while being copied")
                    os.replace(stage, retained)
                if digest(retained) != candidate_hash:
                    raise PinRefused("Retained candidate hash is corrupted")
                # Verify the exact bytes about to execute, after retaining them.
                # A trusted folder alone cannot authorize a replaced executable.
                signature = self.signature(retained)
                if (
                    signature.get("status") != "Valid"
                    or signature.get("publisher") != "OpenAI OpCo, LLC"
                ):
                    raise PinRefused("Candidate publisher signature is not valid OpenAI OpCo, LLC")
                if digest(retained) != candidate_hash or digest(candidate) != candidate_hash:
                    raise PinRefused("Candidate changed during publisher verification")
                version = self.version(retained)
                print("Runtime candidate: " + version, file=sys.stderr)
                change["new_version"] = version
                if rollback is None:
                    permit_version(
                        pinned["version"], version, candidate_hash == pinned["binary_sha256"]
                    )
                elif version != previous[0]["version"]:
                    raise PinRefused("Previous runtime version disagrees with its receipt")
                results = self.gate_results(self.probe(retained))
                if digest(retained) != candidate_hash or digest(candidate) != candidate_hash:
                    raise PinRefused("Candidate changed during verification")
                if self.read_locks() != old or inputs != {
                    name: digest(self.here / name) for name in CATALOGS + INVENTORIES
                }:
                    raise PinRefused("Pins or probe contracts changed during verification")
                target = (
                    pinned["binary"]
                    if valid and candidate_hash == pinned["binary_sha256"]
                    else retained.as_posix()
                )
                new = [
                    {**lock, "binary": target, "binary_sha256": candidate_hash, "version": version}
                    for lock in old
                ]
                receipt = uuid.uuid4().hex
                history = self.state / "history" / receipt
                history.mkdir(parents=True)
                atomic_json(history / "previous.json", old)
                report = {
                    "date": datetime.now(UTC).isoformat(),
                    "receipt": receipt,
                    "action": "rollback" if rollback else ("revalidated" if valid else "repinned"),
                    "old_hash": pinned["binary_sha256"],
                    "old_version": pinned["version"],
                    "new_hash": candidate_hash,
                    "new_version": version,
                    "installed_source": str(candidate),
                    "signature": signature,
                    "probes": results,
                    "status": "verified; publication pending",
                }
                atomic_json(history / "verified.json", report)
                # Durable visible proof is required BEFORE allowing new agents.
                self.record("verified", receipt, report)
                atomic_json(self.state / "transaction.json", {"old": old, "new": new})
                try:
                    for name, lock in zip(LOCKS, new, strict=True):
                        atomic_json(self.here / name, lock)
                except BaseException:
                    for name, lock in zip(LOCKS, old, strict=True):
                        atomic_json(self.here / name, lock)
                    raise
                (self.state / "transaction.json").unlink()
                report["status"] = "published"
                atomic_json(history / "published.json", report)
                # This second append can be replayed safely after a door timeout.
                try:
                    self.record("published", receipt + "-pub", report)
                except Exception:
                    atomic_json(self.state / ("pending-" + receipt + ".json"), report)
                return new[0]
            except Exception as error:
                reason = str(error) if isinstance(error, PinRefused) else type(error).__name__
                # Stable fingerprints suppress duplicate banners across both adapters.
                key = hashlib.sha256(key.encode()).hexdigest()
                notice = self.state / ("notice-" + key + ".json")
                if not notice.exists():
                    report = {**change, "reason": reason, "date": datetime.now(UTC).isoformat()}
                    # Retrying after a lost response uses the SAME world gesture.
                    try:
                        self.record("notice", key, report)
                    except Exception as record_error:
                        report["record_error"] = f"{type(record_error).__name__}: {record_error}"
                        atomic_json(self.state / ("pending-notice-" + key + ".json"), report)
                    else:
                        atomic_json(notice, report)
                raise PinRefused(reason) from error

    def printed_version(self, binary):
        from probe_support import isolated_environment, probe_directory

        # Even --version is executed with an empty home, without loading auth.
        with probe_directory() as directory:
            # Do not mutate the adapter parent's environment.
            profile = Path(directory) / "empty-home"
            profile.mkdir()
            env = isolated_environment(directory, profile)
            result = subprocess.run(
                [str(binary), "--version"],
                capture_output=True,
                text=True,
                timeout=20,
                env=env,
                cwd=directory,
            )
            if result.returncode:
                raise PinRefused("Candidate --version failed")
            version = result.stdout.strip()
            version_key(version)
            return version

    def probe_runtime(self, binary):
        from probe_support import isolated_environment, probe_directory

        if importlib.metadata.version("openai-codex") != self.read_locks()[0]["sdk"]:
            raise PinRefused("Installed SDK differs from the pinned SDK")
        with probe_directory() as directory:
            output = Path(directory)
            inventories = []
            runs = (
                ("resident", "gpt-6-astra"),
                ("worker", "gpt-6.1-sol"),
                ("worker", "gpt-6-astra"),
            )
            for kind, model in runs:
                path = output / (kind + "-" + model + ".json")
                script = "probe_runtime.py" if kind == "resident" else "probe_worker.py"
                # Even the Python probe starts without a route to the real home.
                profile = output / (kind + "-" + model + "-home")
                profile.mkdir()
                env = isolated_environment(directory, profile)
                result = subprocess.run(
                    [
                        sys.executable,
                        "-E",
                        str(self.here / script),
                        "--binary",
                        str(binary),
                        "--output",
                        str(path),
                        "--model",
                        model,
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=100,
                )
                if result.returncode or "PASS:" not in result.stdout or not path.is_file():
                    # Keep diagnostics local; banners don't dump model requests.
                    diagnostic = self.state / "last-probe-failure.txt"
                    diagnostic.write_text(result.stdout + result.stderr, encoding="utf-8")
                    raise PinRefused(
                        f"{kind} mock probe failed for {model}; "
                        "JEFF must review the local probe diagnostic"
                    )
                actual = json.loads(path.read_text(encoding="utf-8"))
                inventories.append({"kind": kind, "model": model, "inventory": actual})
            return {"passed": True, "runs": inventories}


def worker_record_url(mcp):
    servers = json.loads(Path(mcp).read_text(encoding="utf-8"))["mcpServers"]
    if set(servers) != {"desk"}:
        raise PinRefused("Runtime checks require the worker's authorized Desk configuration")
    # Workshop deliberately sets DESKD=off for local shell commands. Its
    # already-authorized MCP child holds the actual door address.
    return servers["desk"].get("env", {}).get("DESKD", "off")


def ensure_runtime(record_url=None):
    return Checker(record=WorldRecord(record_url)).check()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recheck", action="store_true", help="Certify the current pin again, including all probes"
    )
    parser.add_argument(
        "--rollback", help="Checker receipt id; previous bytes must pass all current probes again"
    )
    parser.add_argument(
        "--mcp-config", type=Path, help="Use the existing worker Desk route without changing DESKD"
    )
    args = parser.parse_args()
    try:
        record_url = worker_record_url(args.mcp_config) if args.mcp_config else None
        lock = Checker(record=WorldRecord(record_url)).check(args.recheck, args.rollback)
    except PinRefused as error:
        print("REFUSED: " + str(error), file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps({"version": lock["version"], "sha256": lock["binary_sha256"]}))


if __name__ == "__main__":
    main()
