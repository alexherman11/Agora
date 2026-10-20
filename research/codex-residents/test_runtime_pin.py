"""Updates use fake executables/inventories. No account, live model or Desk."""

import builtins
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest
import runtime_pin as pin


@pytest.fixture
def fixture():
    # Inherited Windows ACLs, so child processes can also use these fixtures.
    root = Path(__file__).resolve().parents[2] / "local" / ("pin-test-" + uuid.uuid4().hex)
    here, installs = root / "source", root / "bin"
    here.mkdir(parents=True)
    installs.mkdir()
    old = installs / "old" / "codex.exe"
    old.parent.mkdir()
    old.write_bytes(b"old fake executable")
    candidate = installs / "new" / "codex.exe"
    candidate.parent.mkdir()
    candidate.write_bytes(b"benign update fake executable")
    resident = {
        "model": "gpt-6-astra",
        "tools": [],
        "messages": [{"role": "user", "content": "fixture"}],
        "reply": [{"type": "result", "is_error": False, "result": "> look\n> rest"}],
    }
    worker = {
        "model": "gpt-6.1-sol",
        "tools": [{"type": "function", "name": "fixture_tool", "parameters": {"type": "object"}}],
    }
    for name, inventory in zip(pin.INVENTORIES, (resident, worker), strict=True):
        pin.atomic_json(here / name, inventory)
    for name in pin.CATALOGS:
        (here / name).write_bytes(b'{"models":[]}\r\n')
    locks = []
    for name, catalog in zip(pin.LOCKS, pin.CATALOGS, strict=True):
        value = {
            "binary": str(old),
            "binary_sha256": pin.digest(old),
            "version": "codex-cli 0.162.0-alpha.17.2",
            "sdk": "fixture",
            "catalog_sha256": pin.digest(here / catalog),
        }
        pin.atomic_json(here / name, value)
        locks.append(value)
    calls = []

    def probe(binary):
        calls.append(("probe", pin.digest(binary)))
        return {
            "passed": True,
            "runs": [
                {"kind": "resident", "model": "gpt-6-astra", "inventory": copy.deepcopy(resident)},
                {"kind": "worker", "model": "gpt-6.1-sol", "inventory": copy.deepcopy(worker)},
                {
                    "kind": "worker",
                    "model": "gpt-6-astra",
                    "inventory": {**copy.deepcopy(worker), "model": "gpt-6-astra"},
                },
            ],
        }

    def record(kind, key, value):
        calls.append((kind, key, value))

    checker = pin.Checker(
        here,
        root / "state",
        installs,
        record=record,
        probe=probe,
        version=lambda binary: "codex-cli 0.163.0-alpha.10.2",
        signature=lambda binary: {"status": "Valid", "publisher": "OpenAI OpCo, LLC"},
    )
    yield root, old, candidate, checker, calls, locks
    shutil.rmtree(root)


def read_locks(checker):
    return [json.loads((checker.here / n).read_text()) for n in pin.LOCKS]


def test_healthy_pin_never_executes_or_notifies(fixture):
    _, _, _, checker, calls, original = fixture
    assert checker.check() == original[0]
    assert calls == []


@pytest.mark.parametrize("status,publisher", [
    ("NotSigned", ""),
    ("HashMismatch", "OpenAI OpCo, LLC"),
    ("Valid", "Unrelated Publisher"),
])
def test_untrusted_publisher_refuses_before_execution(fixture, status, publisher):
    _, old, _, checker, calls, original = fixture
    old.unlink()
    checker.signature = lambda _: {"status": status, "publisher": publisher}
    checker.version = lambda _: pytest.fail("Untrusted candidate executed")
    with pytest.raises(pin.PinRefused, match="publisher signature"):
        checker.check()
    assert read_locks(checker) == original
    assert [c[0] for c in calls] == ["notice"]


def test_outside_install_refuses_before_signature_or_execution(fixture):
    root, old, _, checker, calls, original = fixture
    old.unlink()
    outside = root / "untrusted" / "codex.exe"
    outside.parent.mkdir()
    outside.write_bytes(b"untrusted executable")
    checker.candidate = lambda _: outside
    checker.signature = lambda _: pytest.fail("Outside candidate inspected")
    checker.version = lambda _: pytest.fail("Outside candidate executed")
    with pytest.raises(pin.PinRefused, match="outside Codex's own bin folder"):
        checker.check()
    assert read_locks(checker) == original
    assert [c[0] for c in calls] == ["notice"]


def test_retained_copy_requires_identical_updater_install(fixture):
    root, old, candidate, checker, _, _ = fixture
    retained = root / "retained" / "codex.exe"
    retained.parent.mkdir()
    retained.write_bytes(candidate.read_bytes())
    assert checker.installed_source(retained, pin.digest(retained)) == candidate
    candidate.unlink()
    old.unlink()
    with pytest.raises(pin.PinRefused, match="no identical install"):
        checker.installed_source(retained, pin.digest(retained))


def test_signature_mutation_refuses_before_execution(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()

    def mutate(binary):
        binary.write_bytes(b"changed during signature verification")
        return {"status": "Valid", "publisher": "OpenAI OpCo, LLC"}

    checker.signature = mutate
    checker.version = lambda _: pytest.fail("Changed candidate executed")
    with pytest.raises(pin.PinRefused, match="changed during publisher verification"):
        checker.check()
    assert read_locks(checker) == original


def test_authenticode_uses_windows_verifier_without_executing_candidate(fixture):
    _, _, candidate, _, _, _ = fixture
    seen = []

    def verify(command, **kwargs):
        seen.append(command)
        assert Path(command[0]).name == "powershell.exe"
        assert "-NoProfile" in command and "-NonInteractive" in command
        script = pin.base64.b64decode(command[-1]).decode("utf-16-le")
        assert "Get-AuthenticodeSignature -LiteralPath $env:AGORA_PIN_CANDIDATE" in script
        assert kwargs["env"]["AGORA_PIN_CANDIDATE"] == str(candidate)
        return subprocess.CompletedProcess(
            command, 0, '{"status":"Valid","publisher":"OpenAI OpCo, LLC"}'
        )

    with patch.object(pin.subprocess, "run", side_effect=verify):
        assert pin.authenticode(candidate)["status"] == "Valid"
    assert len(seen) == 1


def test_checker_opens_only_empty_probe_homes_with_real_home_present(fixture):
    """Guard Python file IO; child launch is a stand-in, not a native IO audit."""
    import codex_resident
    import probe_support

    root, old, candidate, checker, _, _ = fixture
    old.unlink()
    fake_home = root / "signed-in-home"
    fake_home.mkdir()
    (fake_home / "auth.json").write_text("DO NOT READ: fake credential sentinel")
    guarded = [Path.home().resolve(), codex_resident.PROFILE.resolve(), fake_home]
    if os.environ.get("CODEX_HOME"):
        guarded.append(Path(os.environ["CODEX_HOME"]).resolve())
    # Stat only: do not enumerate or open the real home or any credential.
    assert Path.home().is_dir()
    opens = []
    launches = []
    inventories = checker.probe(candidate)["runs"]

    def guard_open(original):
        def guarded_open(file, *args, **kwargs):
            if isinstance(file, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(file)).resolve()
                assert not any(path.is_relative_to(home) for home in guarded), (
                    "Checker attempted a signed-in home read"
                )
                opens.append(path)
            return original(file, *args, **kwargs)
        return guarded_open

    def child(command, **kwargs):
        env = kwargs["env"]
        home = Path(env["CODEX_HOME"])
        assert home.is_dir() and not list(home.iterdir())
        assert not any(home.is_relative_to(path) for path in guarded)
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            assert env[name] == str(home)
        assert "OPENAI_API_KEY" not in env
        assert not any(k.startswith("CODEX_") and k != "CODEX_HOME" for k in env)
        launches.append(home)
        if "--version" in command:
            return subprocess.CompletedProcess(command, 0, "codex-cli 0.163.0-alpha.10.2", "")
        output = Path(command[command.index("--output") + 1])
        model = command[command.index("--model") + 1]
        kind = "resident" if Path(command[2]).name == "probe_runtime.py" else "worker"
        inventory = next(
            r["inventory"] for r in inventories if (r["kind"], r["model"]) == (kind, model)
        )
        output.write_text(json.dumps(inventory))
        return subprocess.CompletedProcess(command, 0, "PASS: stand-in", "")

    checker.version = checker.printed_version
    checker.probe = checker.probe_runtime
    with (
        patch.dict(os.environ, {
            "CODEX_HOME": str(fake_home), "HOME": str(fake_home),
            "OPENAI_API_KEY": "fake-secret", "CODEX_UNREVIEWED_FLAG": "1",
        }),
        patch.object(builtins, "open", side_effect=guard_open(builtins.open)),
        patch.object(io, "open", side_effect=guard_open(io.open)),
        patch.object(os, "open", side_effect=guard_open(os.open)),
        patch.object(pin.subprocess, "run", side_effect=child),
        patch.object(pin.importlib.metadata, "version", return_value="fixture"),
    ):
        checker.check()
    assert len(launches) == 4 and len(set(launches)) == 4
    assert opens
    # Also check the SDK probe's own profile redirect, without mutating this test.
    scratch = root / "probe-process"
    scratch.mkdir()
    with patch.dict(os.environ, dict(os.environ)):
        profile = probe_support.empty_profile(scratch)
        assert os.environ["CODEX_HOME"] == str(profile)
        assert os.environ["USERPROFILE"] == str(profile)


def test_benign_update_repins_both_and_keeps_previous(fixture):
    _, old, candidate, checker, calls, original = fixture
    old.unlink()
    approved = checker.check()
    assert approved["binary_sha256"] == pin.digest(candidate)
    assert read_locks(checker) == [approved, approved]
    snapshot = next((checker.state / "history").glob("*/previous.json"))
    assert json.loads(snapshot.read_text()) == original
    assert [c[0] for c in calls] == ["probe", "verified", "published"]
    assert Path(approved["binary"]).read_bytes() == candidate.read_bytes()


def test_changed_tool_schema_refuses_and_notifies_once(fixture):
    _, old, _, checker, calls, original = fixture
    old.unlink()
    probe = checker.probe

    def changed(binary):
        result = probe(binary)
        result["runs"][1]["inventory"]["tools"][0]["parameters"]["required"] = ["unexpected"]
        return result

    checker.probe = changed
    for _ in range(2):
        with pytest.raises(pin.PinRefused, match="tool declarations changed"):
            checker.check()
    assert read_locks(checker) == original
    assert len([c for c in calls if c[0] == "notice"]) == 1
    assert not list((checker.state / "history").glob("*/previous.json"))


def test_missing_binary_refuses(fixture):
    _, old, candidate, checker, calls, original = fixture
    old.unlink()
    candidate.unlink()
    with pytest.raises(pin.PinRefused, match="no installed candidate"):
        checker.check()
    assert read_locks(checker) == original
    assert [c[0] for c in calls] == ["notice"]


def test_corrupt_hash_does_not_bless_same_version(fixture):
    _, old, candidate, checker, calls, original = fixture
    old.write_bytes(b"tampered old executable")
    candidate.write_bytes(b"tampered replacement")
    # File timestamp resolution must not choose the corrupted old installation.
    os.utime(old, (1, 1))
    os.utime(candidate, (2, 2))
    checker.version = lambda _: original[0]["version"]
    with pytest.raises(pin.PinRefused, match="Not a forward"):
        checker.check()
    assert read_locks(checker) == original
    assert not any(c[0] == "probe" for c in calls)


def test_corrupt_pinned_binary_cannot_approve_itself(fixture):
    _, old, candidate, checker, _, original = fixture
    old.write_bytes(b"corrupt pinned binary")
    candidate.unlink()
    checker.signature = lambda _: pytest.fail("Corrupt pin inspected for approval")
    checker.version = lambda _: pytest.fail("Corrupt pin executed")
    with pytest.raises(pin.PinRefused, match="hash is corrupted"):
        checker.check()
    assert read_locks(checker) == original


def test_major_jump_refuses_before_probes(fixture):
    _, old, _, checker, calls, original = fixture
    old.unlink()
    checker.version = lambda _: "codex-cli 1.0.0"
    with pytest.raises(pin.PinRefused, match="Major version"):
        checker.check()
    assert read_locks(checker) == original
    assert not any(c[0] == "probe" for c in calls)


def test_failed_probe_leaves_locks_and_no_success_record(fixture):
    _, old, _, checker, calls, original = fixture
    old.unlink()
    checker.probe = lambda _: {"passed": False}
    with pytest.raises(pin.PinRefused, match="did not all pass"):
        checker.check()
    assert read_locks(checker) == original
    assert [c[0] for c in calls] == ["notice"]


def test_candidate_mutation_during_probe_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def mutate(binary):
        result = probe(binary)
        binary.write_bytes(b"changed while checking")
        return result

    checker.probe = mutate
    with pytest.raises(pin.PinRefused, match="changed during verification"):
        checker.check()
    assert read_locks(checker) == original


def test_injected_prompt_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def inject(binary):
        result = probe(binary)
        result["runs"][0]["inventory"]["messages"].append(
            {"role": "developer", "content": "surprise"}
        )
        return result

    checker.probe = inject
    with pytest.raises(pin.PinRefused, match="injected instructions"):
        checker.check()
    assert read_locks(checker) == original


def test_world_record_failure_cannot_publish(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    checker.record = lambda *args: (_ for _ in ()).throw(OSError("door unavailable"))
    with pytest.raises(pin.PinRefused):
        checker.check()
    assert read_locks(checker) == original
    assert list(checker.state.glob("pending-notice-*.json"))


def test_two_lock_publication_failure_rolls_back(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    writer = pin.atomic_json
    failed = False

    def fail_once(path, value):
        nonlocal failed
        if Path(path) == checker.here / pin.LOCKS[1] and not failed:
            failed = True
            raise OSError("simulated second-lock publication failure")
        writer(path, value)

    with patch.object(pin, "atomic_json", fail_once):
        with pytest.raises(pin.PinRefused):
            checker.check()
    assert read_locks(checker) == original
    checker.recover()
    assert read_locks(checker) == original


def test_crash_journal_restores_both_before_returning(fixture):
    _, _, _, checker, calls, original = fixture
    checker.state.mkdir()
    changed = [{**v, "version": "codex-cli 0.999.0"} for v in original]
    pin.atomic_json(checker.state / "transaction.json", {"old": original, "new": changed})
    pin.atomic_json(checker.here / pin.LOCKS[0], changed[0])
    assert checker.check() == original[0]
    assert read_locks(checker) == original
    assert calls == []


def test_completed_transaction_is_not_rolled_back(fixture):
    _, _, _, checker, _, original = fixture
    checker.state.mkdir()
    pin.atomic_json(checker.state / "transaction.json", {"old": [], "new": original})
    assert checker.check() == original[0]


def test_previous_pin_is_reversible_but_reprobed(fixture):
    _, old, candidate, checker, calls, original = fixture
    # Certify current first, retaining the original executable.
    checker.version = lambda _: original[0]["version"]
    checker.check(recheck=True)
    first_receipt = next(c[1] for c in calls if c[0] == "verified")
    # Temporarily remove the old executable to cause discovery, then restore
    # its original bytes for the explicit rollback.
    old_bytes = old.read_bytes()
    old.unlink()
    checker.version = lambda _: "codex-cli 0.163.0"
    checker.check()
    old.write_bytes(old_bytes)
    checker.version = lambda _: original[0]["version"]
    checker.check(rollback=first_receipt)
    assert read_locks(checker)[0]["binary_sha256"] == pin.digest(old)
    assert len([c for c in calls if c[0] == "probe"]) == 3


def test_source_candidate_mutation_during_probe_refuses(fixture):
    _, old, candidate, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def mutate(binary):
        result = probe(binary)
        candidate.write_bytes(b"source changed during verification")
        return result

    checker.probe = mutate
    with pytest.raises(pin.PinRefused, match="changed during verification"):
        checker.check()
    assert read_locks(checker) == original


def test_contract_mutation_during_probe_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def mutate(binary):
        result = probe(binary)
        (checker.here / pin.INVENTORIES[0]).write_text('{"tools":[]}')
        return result

    checker.probe = mutate
    with pytest.raises(pin.PinRefused, match="contracts changed"):
        checker.check()
    assert read_locks(checker) == original


def test_tool_addition_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def add_tool(binary):
        result = probe(binary)
        result["runs"][2]["inventory"]["tools"].append({"type": "function", "name": "unreviewed"})
        return result

    checker.probe = add_tool
    with pytest.raises(pin.PinRefused, match="tool declarations changed"):
        checker.check()
    assert read_locks(checker) == original


def test_incomplete_probe_matrix_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe
    checker.probe = lambda binary: {**probe(binary), "runs": []}
    with pytest.raises(pin.PinRefused, match="matrix is incomplete"):
        checker.check()
    assert read_locks(checker) == original


def test_mutex_excludes_a_second_process(fixture):
    root, _, _, checker, _, _ = fixture
    marker = root / "child-locked"
    script = (
        "import sys,time\n"
        f"sys.path.insert(0,{str(pin.HERE)!r})\n"
        "from runtime_pin import mutex\n"
        "from pathlib import Path\n"
        f"with mutex(Path({str(checker.state)!r})):\n"
        f"    Path({str(marker)!r}).write_text('locked')\n"
        "    time.sleep(0.5)\n"
    )
    proc = subprocess.Popen([sys.executable, "-c", script])
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists(), "Child did not acquire the checker lock"
        began = time.monotonic()
        with pin.mutex(checker.state):
            assert time.monotonic() - began >= 0.3
        assert proc.wait(timeout=10) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def test_world_record_uses_role_lookup_and_one_unaddressed_notice():
    calls, gestures = [], set()

    class Door(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            line = body["line"]
            assert body["as"] == "runtime-pins" and body["session"] == "frontier"
            if line == "find role=notifications":
                text = 'find: 1 thing(s)\n  in f01 "Board":\n    a10 chat "Notifications sent"\n'
            elif line == "find role=runtime-pins":
                text = 'find: 1 thing(s)\n  in f02 "Handbook":\n    a11 note "Runtime pins"\n'
            elif line.startswith("read "):
                assert line in ("read a10 tail=1", "read a11")
                text = "fixture text"
            else:
                text = "ok"
            if body.get("gesture") and body["gesture"] not in gestures:
                gestures.add(body["gesture"])
                calls.append(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"text": text}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Door)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        sink = pin.WorldRecord()
        sink.url = f"http://127.0.0.1:{server.server_port}"
        for _ in range(2):
            sink("notice", "fixture", {"reason": "fixture probe failed"})
        sink("verified", "receipt", {"status": "verified; publication pending"})
        assert len(calls) == 2
        assert calls[0]["line"].startswith("do append a10 ")
        assert calls[0]["line"].endswith(" to=nobody")
        assert calls[1]["line"].startswith("do append a11 ")
        assert calls[0]["gesture"] == "pin-notice-fixture"
    finally:
        server.shutdown()
        server.server_close()


def test_worker_uses_existing_mcp_route_while_shell_deskd_stays_off(fixture, monkeypatch):
    import codex_worker

    root, _, _, _, _, _ = fixture
    mcp = root / "worker-mcp.json"
    pin.atomic_json(mcp, {"mcpServers": {"desk": {"env": {"DESKD": "http://127.0.0.1:8794"}}}})
    monkeypatch.setenv("DESKD", "off")
    with patch.object(pin, "ensure_runtime", side_effect=RuntimeError("captured gate")) as check:
        with pytest.raises(RuntimeError, match="captured gate"):
            codex_worker.runtime_config(root, mcp=mcp)
        check.assert_called_once_with(record_url="http://127.0.0.1:8794")
    assert pin.os.environ["DESKD"] == "off"


def test_world_record_refuses_external_endpoint_before_io(monkeypatch):
    monkeypatch.setenv("DESKD", "http://example.invalid")
    with patch.object(pin, "build_opener") as network:
        with pytest.raises(pin.PinRefused, match="local house door"):
            pin.WorldRecord().act("look")
        network.assert_not_called()


def test_probe_refuses_optimized_assertions():
    result = subprocess.run(
        [sys.executable, "-O", str(pin.HERE / "probe_runtime.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode != 0
    assert "Probe assertions must be enabled" in result.stderr


def test_probe_output_cannot_overwrite_a_lock():
    lock = pin.HERE / pin.LOCKS[0]
    before = pin.digest(lock)
    result = subprocess.run(
        [
            sys.executable,
            str(pin.HERE / "probe_runtime.py"),
            "--binary",
            "unused",
            "--output",
            str(lock),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "must not overwrite trusted runtime files" in result.stderr
    assert pin.digest(lock) == before


def test_model_substitution_refuses(fixture):
    _, old, _, checker, _, original = fixture
    old.unlink()
    probe = checker.probe

    def substitute(binary):
        result = probe(binary)
        result["runs"][0]["inventory"]["model"] = "another-model"
        return result

    checker.probe = substitute
    with pytest.raises(pin.PinRefused, match="model was substituted"):
        checker.check()
    assert read_locks(checker) == original


def test_catalog_content_change_refuses_but_lf_checkout_is_allowed(fixture):
    _, _, _, checker, _, original = fixture
    catalog = checker.here / pin.CATALOGS[0]
    catalog.write_bytes(catalog.read_bytes().replace(b"\r\n", b"\n"))
    assert checker.check() == original[0]
    catalog.write_bytes(b'{"models":["unreviewed"]}\n')
    with pytest.raises(pin.PinRefused, match="catalog changed"):
        checker.check()


@pytest.mark.parametrize(
    "old,new,allowed",
    [
        ("0.162.0", "0.163.0", True),
        ("0.163.0-alpha.9", "0.163.0-alpha.10.2", True),
        ("0.163.0", "0.163.0-alpha.11", False),
        ("0.163.1", "0.163.0", False),
        ("0.163.0", "1.0.0", False),
        ("0.163.0", "0.163.0", False),
    ],
)
def test_version_policy(old, new, allowed):
    if allowed:
        pin.permit_version("codex-cli " + old, "codex-cli " + new)
    else:
        with pytest.raises(pin.PinRefused):
            pin.permit_version("codex-cli " + old, "codex-cli " + new)
