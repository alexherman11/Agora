"""Real Git fixtures only, under the worktree's .tmp; never adopt the real main."""

import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(HERE), str(LAB), str(LAB.parent / "desktop/kernel-desktop")]
import adopt as A  # noqa: E402
import builders as B  # noqa: E402
import house as H  # noqa: E402
from kernel import lines  # noqa: E402
from kernel.kernel import Kernel  # noqa: E402


def git(repo, *args, env=None):
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True,
        env=env or A.clean_env(),
        stdin=subprocess.DEVNULL,
        creationflags=A.T.NO_WINDOW,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout


@pytest.fixture
def fixture(monkeypatch):
    root = LAB.parents[1] / ".tmp" / ("adopt-" + uuid.uuid4().hex)
    repo = root / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Alex Fixture")
    git(repo, "config", "user.email", "alex-fixture@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    for file in ("owned.py", "other.py", "clean.py", "with space.py", "[literal].py"):
        (repo / file).write_text("value = 1\n")
    (repo / "test_baseline.py").write_text("def test_main():\n    assert True\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture base")
    (repo / "owned.py").write_text("value = 2\n")
    b = SimpleNamespace(
        repo=repo,
        steward=lambda person: person == "owner",
        landing_blocker=lambda: "",
        landing_lock=threading.Lock(),
        landing_queue_lock=threading.Lock(),
        git_lock=threading.Lock(),
        land_controls={},
        settings=lambda: {},
    )
    h = H.House.__new__(H.House)
    h.builders, h.home = b, root / "house"
    h.ready = threading.Event()
    h.ready.set()
    h.m = SimpleNamespace(accept=Mock())
    monkeypatch.setattr(B, "CHECKS", [["test_baseline.py"]])
    monkeypatch.setattr(A.T, "PY", Path(sys.executable))
    return SimpleNamespace(h=h, repo=repo, base=git(repo, "rev-parse", "HEAD"))


def call(f, files=None, **kv):
    files = ["owned.py"] if files is None else files
    return f.h.call(
        dict(
            word="house.adopt",
            use=uuid.uuid4().hex,
            caller={"person": "owner"},
            args={
                "words": " ".join(files),
                "positional": files,
                "kv": kv
                or {"text": "Keep Alex's edits\n\nSource: word\nMissing-word: house.adopt"},
            },
        )
    )


def test_pass_commits_tested_files_as_configured_author_only(fixture, monkeypatch):
    f = fixture
    (f.repo / "other.py").write_text("staged = 2\n")
    git(f.repo, "add", "other.py")
    (f.repo / "other.py").write_text("unstaged = 3\n")
    (f.repo / "untracked.txt").write_bytes(b"keep these exact bytes\r\n")
    nested = f.repo / "unnamed-repository"
    nested.mkdir()
    git(nested, "init")
    (nested / "kept.txt").write_text("untouched")
    original = (
        git(f.repo, "ls-files", "--stage", "--", "other.py"),
        (f.repo / "other.py").read_bytes(),
        (f.repo / "untracked.txt").read_bytes(),
    )
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Wrong inherited author")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "wrong@example.invalid")
    result = call(f)
    assert "refused" not in result, result
    (r,) = result["rows"]
    assert r["status"] == "committed" and r["files"] == ["owned.py"]
    assert r["checks"][0]["status"] == "passed"
    assert "1 passed" in Path(r["checks"][0]["evidence"]).read_text()
    assert git(f.repo, "show", "--format=", "--name-only", "HEAD").strip() == b"owned.py"
    assert (
        git(f.repo, "show", "-s", "--format=%an <%ae>").strip()
        == b"Alex Fixture <alex-fixture@example.invalid>"
    )
    assert (
        git(f.repo, "show", "-s", "--format=%B").decode().strip()
        == "Keep Alex's edits\n\nSource: word\nMissing-word: house.adopt"
    )
    assert git(f.repo, "status", "--porcelain", "--", "owned.py") == b""
    assert original == (
        git(f.repo, "ls-files", "--stage", "--", "other.py"),
        (f.repo / "other.py").read_bytes(),
        (f.repo / "untracked.txt").read_bytes(),
    )
    assert (nested / "kept.txt").read_text() == "untouched"
    assert f.h.m.accept.call_count == 1
    saved = A.receipts(f.h, {"use": "read", "caller": {"person": "owner"}})
    assert saved["rows"][0] == r


def test_baseline_fail_preserves_head_index_and_edits(fixture):
    f = fixture
    (f.repo / "test_baseline.py").write_text("def test_main():\n    assert False\n")
    git(f.repo, "add", "owned.py")
    (f.repo / "owned.py").write_text("value = 3\n")
    index = (f.repo / ".git/index").read_bytes()
    before = git(f.repo, "status", "--porcelain")
    result = call(f)
    assert "baseline failed: House baseline 1" in result["refused"]
    assert git(f.repo, "rev-parse", "HEAD") == f.base
    assert (f.repo / ".git/index").read_bytes() == index
    assert (f.repo / "owned.py").read_text() == "value = 3\n"
    assert git(f.repo, "status", "--porcelain") == before
    assert result["rows"][0]["commit"] is None
    assert result["rows"][0]["checks"][0]["status"] == "failed"


@pytest.mark.parametrize(
    "file",
    [
        "clean.py",
        "../outside.py",
        "/outside.py",
        ".git/config",
        "missing.py",
        ".",
        "C:/outside.py",
        "",
    ],
)
def test_invalid_or_unchanged_paths_refuse_without_commit(fixture, file):
    result = call(fixture, ["owned.py", file])
    assert "refused" in result, result
    assert git(fixture.repo, "rev-parse", "HEAD") == fixture.base
    assert (fixture.repo / "owned.py").read_text() == "value = 2\n"


@pytest.mark.parametrize("name", ["landing_lock", "landing_queue_lock", "git_lock"])
def test_lock_contention_refuses_before_baseline(fixture, name):
    lock = getattr(fixture.h.builders, name)
    with lock:
        result = call(fixture)
    assert "under way" in result["refused"]
    fixture.h.m.accept.assert_not_called()
    assert git(fixture.repo, "rev-parse", "HEAD") == fixture.base


@pytest.mark.parametrize(
    "marker", ["index.lock", "HEAD.lock", "MERGE_HEAD", "refs/heads/main.lock"]
)
def test_external_git_in_progress_refuses(fixture, marker):
    path = fixture.repo / ".git" / marker
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fixture lock")
    result = call(fixture)
    assert "under way" in result["refused"]
    assert path.read_text() == "fixture lock"
    assert git(fixture.repo, "rev-parse", "HEAD") == fixture.base


def test_new_deleted_literal_and_space_paths(fixture):
    f = fixture
    (f.repo / "new.py").write_text("new = 1\n")
    (f.repo / "clean.py").unlink()
    for file in ("with space.py", "[literal].py"):
        (f.repo / file).write_text("value = 5\n")
    selected = ["new.py", "clean.py", "with space.py", "[literal].py"]
    result = call(f, selected)
    assert "refused" not in result, result
    assert set(
        git(f.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD")
        .decode()
        .split("\0")
    ) == set(selected) | {""}
    assert git(f.repo, "status", "--porcelain").strip() == b"M owned.py"


def test_checkout_changed_by_check_is_not_committed(fixture):
    f = fixture
    (f.repo / "test_baseline.py").write_text(
        "from pathlib import Path\n"
        "def test_main():\n"
        "    Path('other.py').write_text('changed during checks\\n')\n"
    )
    result = call(f)
    assert "changed during the baseline" in result["refused"], result
    assert git(f.repo, "rev-parse", "HEAD") == f.base


def test_baseline_owns_all_locks_and_failure_releases_them(fixture, monkeypatch):
    f = fixture
    locks = [f.h.builders.landing_lock, f.h.builders.landing_queue_lock, f.h.builders.git_lock]

    def failed(self):
        assert all(lock.locked() for lock in locks)
        assert (f.repo / ".git/index.lock").exists()
        raise RuntimeError("fixture check could not start")

    monkeypatch.setattr(A.Adoption, "baseline", failed)
    result = call(f)
    assert "could not start" in result["refused"]
    assert not any(lock.locked() for lock in locks)
    assert not (f.repo / ".git/index.lock").exists()
    assert git(f.repo, "rev-parse", "HEAD") == f.base


def test_accepted_result_reaches_requester_and_saved_receipt(fixture):
    agent = SimpleNamespace(wake=Mock())
    fixture.h.agents = {"owner": agent}
    result = call(fixture)
    assert "refused" not in result, result
    assert result["rows"][0]["commit"] in agent.wake.call_args.args[0]


def test_index_install_error_reports_published_commit_and_preserves_lock(fixture, monkeypatch):
    original = A.os.replace

    def fail_index(source, target):
        if Path(target) == fixture.repo / ".git/index":
            raise PermissionError("fixture index installation denied")
        return original(source, target)

    monkeypatch.setattr(A.os, "replace", fail_index)
    result = call(fixture)
    assert "refused" not in result and result["external"], result
    (receipt,) = result["rows"]
    assert receipt["status"] == "committed" and "denied" in receipt["error"]
    assert git(fixture.repo, "rev-parse", "HEAD").decode().strip() == receipt["commit"]
    assert (fixture.repo / ".git/index.lock").exists()


def test_nonsteward_never_accepts_or_runs(fixture):
    result = fixture.h.call(
        dict(
            word="house.adopt",
            use="test",
            caller={"person": "outsider"},
            args={"words": "owned.py", "kv": {"text": "message"}},
        )
    )
    assert "stewards" in result["refused"]
    fixture.h.m.accept.assert_not_called()


def test_lines_offer_permissions_and_quoted_paths(fixture):
    f = fixture
    k = Kernel(
        f.h.home / "world",
        {
            "tag": "ad",
            "name": "Adopt fixture",
            "steward": {"account": "owner", "name": "Owner"},
            "invites_counted_by": "kernel",
            "invites": [{"code": "fixture", "uses": 2}],
            "modules": [
                {
                    "name": "house",
                    "run": ["never-started"],
                    "publishes": "house.*",
                    "grants": "house.* rows look",
                }
            ],
        },
    )
    owner = k.actor_for(k.accounts["owner"])
    mid = k.module_named("house")
    offers = [e for e in H.OFFER if e["word"] in ("house.adopt", "house.adoptions")]
    k.on_offer(mid, offers)
    f.h.builders.steward = k.is_steward

    def module_call(mid, word, args, caller):
        return f.h.call(
            dict(
                word=word,
                args=args,
                use="lines-fixture",
                caller={"person": caller.person, "id": caller.id},
            )
        )

    k.modules = SimpleNamespace(
        running=lambda _: True,
        call=module_call,
        done=Mock(),
        deliver=lambda _: None,
        reconcile=lambda: None,
    )
    (f.repo / "with space.py").write_text("value = 7\n")
    out = k.run(owner, 'house.adopt "with space.py" text="Keep the space path"')
    assert out["ok"], out
    assert out["rows"][0]["files"] == ["with space.py"]
    assert k.run(owner, "house.adoptions")["rows"][0]["commit"]
    outsider = k.actor_for(k.join("outsider", "Other", "fixture")["person"])
    denied = k.run(outsider, 'house.adopt owned.py text="deny"')
    assert not denied["ok"], denied
    assert git(f.repo, "status", "--porcelain").strip() == b"M owned.py"


def test_parser_keeps_file_argument_boundaries():
    step = lines.parse('house.adopt "a b.py" c.py text="the message"')
    assert step.positional == ["a b.py", "c.py"]


def test_unnamed_racy_edit_remains_visible_to_git(fixture):
    f = fixture
    path = f.repo / "other.py"
    stamp = path.stat()
    path.write_text("value = 9\n")
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    index = f.repo / ".git/index"
    os.utime(index, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    before = git(f.repo, "status", "--porcelain", "--", "other.py")
    assert before.strip() == b"M other.py"
    result = call(f)
    assert "refused" not in result, result
    assert path.read_text() == "value = 9\n"
    assert git(f.repo, "status", "--porcelain", "--", "other.py") == before
