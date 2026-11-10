"""Adopt explicitly named main-checkout edits through the House publication gate.

The real index and working files stay untouched until checks pass. Private
indexes build the commit and the replacement index independently, preserving
every unnamed staged entry. No stash, reset, checkout, hooks or history rewrite.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import ExitStack
from pathlib import Path

import landing_control
import review_suites
import transport as T


def allowed(house, msg):
    return bool(msg.get("use") and house.builders.steward((msg.get("caller") or {}).get("person")))


def receipts(house, msg):
    if not allowed(house, msg):
        return {"refused": "house.adoptions is for authenticated stewards"}
    folder = house.home / "adoptions"
    rows = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(
            folder.glob("*/receipt.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
    ]
    return {"text": "\n".join(describe(r) for r in rows) or "No adoption receipts.", "rows": rows}


def describe(receipt):
    return (
        "house.adopt "
        + receipt["request"]
        + ": "
        + receipt["status"]
        + (f" commit {receipt['commit']}" if receipt.get("commit") else "")
        + "\nfiles: "
        + ", ".join(receipt["files"])
        + "\n"
        + review_suites.summary(receipt["checks"])
        + (f"\n{receipt['error']}" if receipt.get("error") else "")
    )


def clean_env():
    # Identity and repository selection come only from the repository's config.
    return {k: v for k, v in T.clean_env("off").items() if not k.upper().startswith("GIT_")}


class Adoption:
    def __init__(self, house, files, message, folder, receipt):
        self.house, self.repo = house, house.builders.repo.resolve()
        self.files, self.message, self.folder, self.receipt = files, message, folder, receipt
        self.control = landing_control.Control(house.builders.settings())
        self.env = clean_env()

    def git(self, *args, env=None, data=None):
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            # Input files avoid pipes and preserve exact message/index bytes.
            with tempfile.TemporaryFile() as inp:
                if data is not None:
                    inp.write(data)
                    inp.seek(0)
                proc = subprocess.Popen(
                    [
                        "git",
                        "--no-optional-locks",
                        "--literal-pathspecs",
                        "--no-replace-objects",
                        "-c",
                        "gc.auto=0",
                        "-c",
                        "maintenance.auto=false",
                        "-C",
                        str(self.repo),
                        *args,
                    ],
                    stdin=inp,
                    stdout=out,
                    stderr=err,
                    env=env or self.env,
                    creationflags=T.NO_WINDOW,
                )
                code = self.control.wait(proc, self.control.policy["landing_wait_timeout"])
            out.seek(0)
            err.seek(0)
            result = out.read()
            if code:
                raise RuntimeError(
                    err.read().decode("utf-8", "replace")[-2000:]
                    or f"git {args[0]} failed ({code})"
                )
            return result

    def git_path(self, name):
        return Path(
            os.fsdecode(self.git("rev-parse", "--path-format=absolute", "--git-path", name)).strip()
        )

    def validate(self):
        if self.git("symbolic-ref", "-q", "HEAD").strip() != b"refs/heads/main":
            raise ValueError("house.adopt requires the main checkout on main")
        if (
            Path(os.fsdecode(self.git("rev-parse", "--show-toplevel")).strip()).resolve()
            != self.repo
        ):
            raise ValueError("repository root does not match the main checkout")
        for marker in (
            "MERGE_HEAD",
            "CHERRY_PICK_HEAD",
            "REVERT_HEAD",
            "rebase-merge",
            "rebase-apply",
            "sequencer",
            "HEAD.lock",
            "refs/heads/main.lock",
            "packed-refs.lock",
        ):
            if self.git_path(marker).exists():
                raise ValueError(f"a git step is under way ({marker})")
        if self.git("ls-files", "--unmerged"):
            raise ValueError("main has unresolved index entries")
        for file in self.files:
            path = self.repo / file
            if (
                not path.resolve().is_relative_to(self.repo)
                or path.is_symlink()
                or path.is_dir()
                or any(p.casefold() == ".git" for p in Path(file).parts)
            ):
                raise ValueError(f"outside repository or not a regular file: {file}")

    def snapshot(self):
        digest = hashlib.sha256(
            self.git(
                "diff", "--binary", "--no-ext-diff", "--no-textconv", "--no-renames", "HEAD", "--"
            )
        )
        # Include staged-only changes and new files, without refreshing the real index.
        digest.update(
            self.git(
                "diff",
                "--cached",
                "--binary",
                "--no-ext-diff",
                "--no-textconv",
                "--no-renames",
                "HEAD",
                "--",
            )
        )
        for raw in self.git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
            if raw:
                path = self.repo / os.fsdecode(raw)
                digest.update(raw + b"\0")
                if path.is_symlink():
                    digest.update(os.readlink(path).encode())
                elif path.is_dir():
                    # Git reports an untracked embedded repository as a directory.
                    # Its internals are outside this checkout's index and selection.
                    digest.update(b"directory")
                else:
                    digest.update(path.read_bytes())
        return digest.digest()

    def baseline(self):
        from builders import CHECKS

        suites = review_suites.plan({}, self.repo, CHECKS)
        if not suites:
            raise ValueError("House baseline is empty")
        for i, suite in enumerate(suites):
            output = self.folder / f"check-{i}.txt"
            command = review_suites.command(suite, T.PY)
            check = dict(
                name=suite["name"],
                tests=suite["paths"],
                command=command,
                status="running",
                evidence=str(output),
                returncode=None,
            )
            self.receipt["checks"].append(check)
            env = clean_env()
            env.update(
                AGORA_TMP=str(self.folder / "tmp"),
                AGORA_REVIEW_EVIDENCE=str(self.folder / f"check-{i}-artifacts"),
                GIT_OPTIONAL_LOCKS="0",
                PYTHONDONTWRITEBYTECODE="1",
            )
            with output.open("w", encoding="utf-8") as stream:
                try:
                    result = self.control.run(
                        command,
                        timeout=suite["timeout"],
                        cwd=self.repo,
                        env=env,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        creationflags=T.NO_WINDOW,
                    )
                    check.update(
                        returncode=result.returncode,
                        status="passed" if result.returncode == 0 else "failed",
                    )
                except Exception as exc:
                    check.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                    stream.write("\n" + check["error"])
            check["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
            save(self.folder, self.receipt)
        failed = [c["name"] for c in self.receipt["checks"] if c["status"] != "passed"]
        if failed:
            raise ValueError("baseline failed: " + ", ".join(failed))

    def run(self):
        self.validate()
        base = self.git("rev-parse", "HEAD").strip()
        index = self.git_path("index")
        lock = index.with_name(index.name + ".lock")
        try:
            handle = lock.open("xb")
        except FileExistsError:
            raise ValueError("a git step is under way (index.lock)") from None
        try:
            with handle:
                name = self.git("config", "--get", "user.name").decode("utf-8").strip()
                email = self.git("config", "--get", "user.email").decode("utf-8").strip()
                if not name or not email:
                    raise ValueError("repository git author identity is missing")
                self.receipt["author"] = {"name": name, "email": email}
                selected_env = dict(self.env, GIT_INDEX_FILE=str(self.folder / "selected-index"))
                self.git("read-tree", base.decode(), env=selected_env)
                self.git("add", "-A", "--", *self.files, env=selected_env)
                changed = self.git(
                    "diff",
                    "--cached",
                    "--name-only",
                    "--no-renames",
                    "-z",
                    base.decode(),
                    env=selected_env,
                ).split(b"\0")
                for file in self.files:
                    if os.fsencode(file) not in changed:
                        raise ValueError(f"named path has no changes to adopt: {file}")
                if {os.fsdecode(p) for p in changed if p} != set(self.files):
                    raise ValueError("selection includes files beyond the named paths")
                tree = self.git("write-tree", env=selected_env).strip()
                before = self.snapshot()
                self.baseline()
                self.validate()
                if self.git("rev-parse", "HEAD").strip() != base or self.snapshot() != before:
                    raise ValueError("main or its edits changed during the baseline; check again")
                # Catch edits between the selected tree and the first snapshot too.
                self.git("read-tree", base.decode(), env=selected_env)
                self.git("add", "-A", "--", *self.files, env=selected_env)
                if self.git("write-tree", env=selected_env).strip() != tree:
                    raise ValueError("named files changed during the baseline; check again")
                next_index = self.folder / "next-index"
                if index.exists():
                    # Git uses the index timestamp to recognise racy-clean entries.
                    # Losing it can hide an unnamed same-size edit when writing back.
                    shutil.copy2(index, next_index)
                next_env = dict(self.env, GIT_INDEX_FILE=str(next_index))
                if not index.exists():
                    self.git("read-tree", base.decode(), env=next_env)
                # Remove selected entries, then install exactly the tested entries.
                self.git("update-index", "--force-remove", "--", *self.files, env=next_env)
                entries = self.git("ls-files", "--stage", "-z", "--", *self.files, env=selected_env)
                self.git("update-index", "-z", "--index-info", env=next_env, data=entries)
                handle.write(next_index.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
                identity = dict(
                    self.env,
                    GIT_AUTHOR_NAME=name,
                    GIT_AUTHOR_EMAIL=email,
                    GIT_COMMITTER_NAME=name,
                    GIT_COMMITTER_EMAIL=email,
                )
                commit = (
                    self.git(
                        "commit-tree",
                        tree.decode(),
                        "-p",
                        base.decode(),
                        env=identity,
                        data=self.message.encode("utf-8"),
                    )
                    .decode()
                    .strip()
                )
                self.git(
                    "update-ref", "-m", "house.adopt", "refs/heads/main", commit, base.decode()
                )
                self.receipt.update(commit=commit, status="committed")
            os.replace(lock, index)
        finally:
            if not self.control.unstopped and not self.receipt.get("commit") and lock.exists():
                lock.unlink()


def save(folder, receipt):
    temp = folder / "receipt.tmp"
    temp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, folder / "receipt.json")


def finish(house, msg, folder, receipt):
    save(folder, receipt)
    agent = getattr(house, "agents", {}).get((msg.get("caller") or {}).get("person"))
    if agent is not None:
        try:
            agent.wake(describe(receipt))
        except Exception as exc:
            # Publication is already settled; a failed notice cannot undo it.
            receipt["notice_error"] = str(exc)
            save(folder, receipt)


def call(house, msg):
    receipt, folder = None, None
    try:
        if not allowed(house, msg):
            raise ValueError("house.adopt is for authenticated stewards")
        args = msg.get("args") or {}
        kv = args.get("kv") or {}
        files = args.get("positional")
        if files is None:
            files = (args.get("words") or "").split()
        message = kv.get("text", "")
        if not files or set(kv) != {"text"} or not isinstance(message, str) or not message.strip():
            raise ValueError("use house.adopt <path> [<path>...] text=<message>")
        files = list(dict.fromkeys(files))
        for file in files:
            if (
                not file
                or "\\" in file
                or ":" in file
                or file.startswith("/")
                or any(ord(c) < 32 for c in file)
                or any(p in ("", ".", "..") for p in file.split("/"))
            ):
                raise ValueError(f"use repository-relative file paths without traversal: {file}")
        builders = house.builders
        blocker = builders.landing_blocker()
        if blocker:
            raise ValueError(blocker)
        with ExitStack() as stack:
            # Match landing's queue -> publication -> git ordering, but never wait.
            for lock, label in (
                (builders.landing_queue_lock, "landing"),
                (builders.landing_lock, "publication"),
                (builders.git_lock, "git step"),
            ):
                if not lock.acquire(blocking=False):
                    raise ValueError(f"a {label} is under way; retry after it finishes")
                stack.callback(lock.release)
            if builders.land_controls:
                raise ValueError("a landing is under way; retry after it finishes")
            folder = house.home / "adoptions" / uuid.uuid4().hex
            folder.mkdir(parents=True)
            receipt = dict(
                request=msg["use"], status="checking", files=files, checks=[], commit=None
            )
            save(folder, receipt)
            house.m.accept(msg)
            adoption = Adoption(house, files, message, folder, receipt)
            try:
                adoption.run()
            finally:
                # A denied child cleanup must not release publication exclusion.
                if (
                    adoption.control.unstopped is not None
                    and adoption.control.unstopped.poll() is None
                ):
                    import threading

                    held = stack.pop_all()

                    def release_after_exit():
                        adoption.control.unstopped.wait()
                        held.close()

                    threading.Thread(target=release_after_exit, daemon=True).start()
        finish(house, msg, folder, receipt)
        return {"text": describe(receipt), "rows": [receipt], "external": True}
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        if receipt is None:
            return {"refused": str(exc)}
        receipt.update(status="committed" if receipt.get("commit") else "refused", error=str(exc))
        finish(house, msg, folder, receipt)
        if receipt.get("commit"):
            return {"text": describe(receipt), "rows": [receipt], "external": True}
        return {"refused": describe(receipt), "rows": [receipt]}
