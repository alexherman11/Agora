"""House-owned, scoped source handoffs. This never lands or executes transferred code.

Called under Workshop's dispatch lock; also takes landing serialization and both
process-held worker leases. Receivers checkpoint their own edits first; conflicts
are computed in Git objects, never left in their files. Main inputs use landing.hand unchanged.
"""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


class Held(RuntimeError):
    pass


def request(raw, recipient):
    try:
        spec = json.loads(raw)
        if set(spec) - {"source", "paths", "request", "after"}:
            raise ValueError("unknown fields")
        if "after" in spec and (not re.fullmatch(r"a[0-9]+", spec["after"]) or spec["after"] == recipient):
            raise ValueError("after must name another receiving card")
        if spec["source"] != "main" and not re.fullmatch(r"a[0-9]+", spec["source"]):
            raise ValueError("source must be main or a card")
        if spec["source"] == recipient:
            raise ValueError("source is recipient")
        if not isinstance(spec["paths"], list) or not 1 <= len(spec["paths"]) <= 200:
            raise ValueError("name 1..200 paths")
        for path in spec["paths"]:
            if not isinstance(path, str):
                raise ValueError("paths must be strings")
            if path == "@preserved":
                if spec["source"] == "main":
                    raise ValueError("main requires explicit paths")
                continue
            safe_path(path.rstrip("/"))
        canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
        return spec, hashlib.sha256((recipient + "\n" + canonical).encode()).hexdigest()
    except (ValueError, TypeError, KeyError) as exc:
        raise Held("invalid brings request: " + str(exc)) from None


def safe_path(text):
    p = PurePosixPath(text)
    parts = p.parts
    if (not text or p.is_absolute() or "\\" in text or ":" in text or
            any(c in text for c in "*?[]") or any(ord(c) < 32 for c in text) or
            any(x in ("", ".", "..") for x in text.split("/")) or
            any(x.endswith((" ", ".")) or
                re.match(r"(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", x) for x in parts) or
            any(x.lower() in (".git", ".worktrees", ".aws", ".ssh", ".azure", "private",
                             "sessions", "house-state", "__pycache__")
                or x.lower().startswith((".env", ".tmp", ".codex", ".claude")) for x in parts)):
        raise Held("not transferable: " + text)
    return p.as_posix()


def git(root, *args, env=None, check=True):
    try:
        r = subprocess.run(["git", "-c", "core.hooksPath=", "-c", "commit.gpgsign=false", *args], cwd=root,
                           env={**os.environ, **(env or {})}, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise Held("git " + args[0] + " timed out; inspect the durable receipt before retry") from None
    if check and r.returncode:
        raise Held("git " + args[0] + ": " + (r.stderr or r.stdout).decode("utf-8", "replace")[-600:])
    return r


def out(root, *args, **kwargs):
    return git(root, *args, **kwargs).stdout.decode("utf-8", "replace").strip()


def head(root):
    return out(root, "rev-parse", "HEAD")


def write_receipt(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def read_receipt(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("phase") not in (
                "receiver-preserving", "receiver-preserved",
                "preserving", "preserved", "conflict", "planned", "applied"):
            raise ValueError("unknown receipt shape")
        if data["phase"] in ("planned", "applied"):
            if not re.fullmatch(r"[0-9a-f]{40,64}", data.get("recipient_after", "")):
                raise ValueError("missing receiver commit")
        checkpoint = data.get("receiver_checkpoint")
        if data["phase"].startswith("receiver-") and not isinstance(checkpoint, dict):
            raise ValueError("missing receiver checkpoint")
        if checkpoint is not None:
            if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("files"), dict):
                raise ValueError("invalid receiver inventory")
            if data["phase"] != "receiver-preserving" and not re.fullmatch(
                    r"[0-9a-f]{40,64}", checkpoint.get("after", "")):
                raise ValueError("missing receiver checkpoint commit")
        return data
    except (ValueError, TypeError):
        raise Held("invalid preserved-work receipt; inspect it before retry") from None


def registered(live, tree, branch):
    if not tree.is_dir():
        raise Held("worktree is absent: " + tree.name)
    common = out(live, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if out(tree, "rev-parse", "--path-format=absolute", "--git-common-dir") != common:
        raise Held("worktree does not belong to this repository")
    # Explicit worktree registry, not merely a directory with a .git entry.
    paths = [x[9:] for x in out(live, "worktree", "list", "--porcelain").splitlines()
             if x.startswith("worktree ")]
    if tree.resolve() not in [Path(x).resolve() for x in paths]:
        raise Held("worktree is not registered")
    if out(tree, "symbolic-ref", "--short", "HEAD") != branch:
        raise Held("worktree is on a different branch")
    if git(tree, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 0:
        raise Held("worktree has an unfinished merge")
    if git(tree, "ls-files", "-u").stdout:
        raise Held("worktree has unmerged files")


def clean_receiver(tree):
    changed = git(tree, "status", "--porcelain", "-z", "--untracked-files=all").stdout.split(b"\0")
    # The house's copied test world is deliberately outside version control.
    if any(x and not x[3:].decode("utf-8", "replace").replace("\\", "/").startswith(
            "research/text-desk-lab/notation/sessions/") for x in changed):
        raise Held("recipient has uncommitted edits; preserve them before bringing work")


def receiver_edits(tree):
    """Inventory both index and worktree, including deletions and rename sides."""
    def names(*args):
        return {p.decode("utf-8") for p in git(tree, *args).stdout.split(b"\0") if p}
    staged = names("diff", "--cached", "--name-only", "--no-renames", "-z", "HEAD")
    changed = staged | names("diff", "--name-only", "--no-renames", "-z")
    changed |= names("ls-files", "-z", "--others", "--exclude-standard")
    sessions = "research/text-desk-lab/notation/sessions/"
    if any(p.startswith(sessions) for p in staged):
        raise Held("recipient index contains session state; not checkpointing it")
    changed = {p for p in changed if not p.startswith(sessions)}
    if len(changed) > 200:
        raise Held("recipient checkpoint exceeds 200 files")
    files, index_files, size = {}, {}, 0
    for name in sorted(changed):
        safe_path(name)
        p = tree / name
        for part in [p, *p.parents]:
            if part == tree:
                break
            if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
                raise Held("recipient checkpoint has a linked path: " + name)
        if p.exists():
            if not p.is_file() or not p.resolve().is_relative_to(tree.resolve()):
                raise Held("recipient checkpoint has a non-file: " + name)
            raw = p.read_bytes()
            size += len(raw)
            files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        else:
            files[name] = {"deleted": True}
        if name in staged:
            entry = git(tree, "ls-files", "--stage", "-z", "--", name).stdout
            if entry:
                if entry.split(b" ", 1)[0] not in (b"100644", b"100755"):
                    raise Held("recipient checkpoint has an unsupported index entry: " + name)
                raw = git(tree, "show", ":" + name).stdout
                size += len(raw)
                index_files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            else:
                index_files[name] = {"deleted": True}
        if size > 32 * 1024 * 1024:
            raise Held("recipient checkpoint exceeds 32 MiB")
    return files, index_files


def checkpoint_receiver(tree, card, receipt_path, data, report):
    """Caller retains the card lease and landing lock through reporting/delivery."""
    saved = data.get("receiver_checkpoint")
    if saved:
        if git(tree, "merge-base", "--is-ancestor", saved["after"], "HEAD", check=False).returncode:
            raise Held("recipient checkpoint needs reconciliation; not replaying")
        clean_receiver(tree)
    else:
        files, staged = receiver_edits(tree)
        if not files:
            clean_receiver(tree)
            return
        saved = {"before": head(tree), "files": files, "index_files": staged}
        data.update(phase="receiver-preserving", receiver_checkpoint=saved)
        write_receipt(receipt_path, data)  # unknown commit outcomes never auto-retry
        # Preserve partial staging too: first commit the existing index, then
        # commit the remaining worktree. Both versions remain in branch history.
        commits = []
        message = f"receiver checkpoint by house for {card}; receipt {data['request']}\n\n"
        if staged:
            git(tree, "commit", "-m", message + json.dumps({"index_files": staged}, sort_keys=True))
            commits.append(head(tree))
        remaining = receiver_edits(tree)[0]
        if set(remaining) - set(files):
            raise Held("recipient changed while checkpointing; inspect receipt")
        if remaining:
            git(tree, "add", "-A", "--", *remaining)
        if git(tree, "diff", "--cached", "--name-only").stdout:
            git(tree, "commit", "-m", message + json.dumps({"files": files}, sort_keys=True))
            commits.append(head(tree))
        clean_receiver(tree)
        if receiver_edits(tree)[0]:
            raise Held("recipient changed while checkpointing; inspect receipt")
        # Record committed blobs separately from raw working bytes.
        committed = {name: ({"deleted": True} if item.get("deleted") else
                            blob_manifest(tree, head(tree), [name])[name])
                     for name, item in files.items()}
        saved.update(after=head(tree), commits=commits, committed_files=committed)
        data["phase"] = "receiver-preserved"
        write_receipt(receipt_path, data)
    if report is not None and not saved.get("reported"):
        report(saved)
        saved["reported"] = True
        write_receipt(receipt_path, data)


def prepare_main(live, tree, card, receipt_path, request_id, report=None, admit=None):
    """Checkpoint and merge only the worker branch, under caller's lease/lock.

    An interrupted merge is unknown, never replayed. The receipt survives a
    house restart; the same request returns its result without another merge.
    """
    if receipt_path.exists():
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        if data.get("request") != request_id:
            raise Held("prepare receipt belongs to another request")
        phase = data.get("phase")
        if phase in ("prepared", "prepare-conflict"):
            if head(tree) != data["after"]:
                raise Held("prepared branch changed before reporting; reconcile receipt")
            return data
        if phase not in ("receiver-preserved", "receiver-preserving", "prepare-started"):
            raise Held("interrupted prepare needs reconciliation; not replaying")
        # Only pre-merge states with a provable checkpoint boundary can resume.
        # Never repeat an unknown commit or merge, or reset anyone's index.
        registered(live, tree, f"worker/{card}")
        saved = data.get("receiver_checkpoint")
        if phase == "receiver-preserved" and saved and head(tree) == saved.get("after"):
            clean_receiver(tree)
        elif phase == "receiver-preserving" and saved and head(tree) == saved.get("before"):
            files, staged = receiver_edits(tree)
            if files != saved["files"]:
                raise Held("interrupted checkpoint files changed; reconciliation required")
            # git add may have completed before a failed commit. Admit only
            # the original index or the exact captured working version.
            captured_index = set(staged) == set(files) and all(
                (item.get("deleted") and staged[name].get("deleted")) or
                (not item.get("deleted") and not staged[name].get("deleted") and
                 out(tree, "hash-object", "--path=" + name, "--", name) ==
                 out(tree, "rev-parse", ":" + name))
                for name, item in files.items())
            if staged != saved.get("index_files", {}) and not captured_index:
                raise Held("interrupted checkpoint index changed; reconciliation required")
            data.setdefault("reconciliations", []).append(
                {"phase": phase, "checkpoint": saved,
                 "reason": "HEAD unchanged; exact captured files/index verified"})
            del data["receiver_checkpoint"]
            write_receipt(receipt_path, data)
        elif phase == "prepare-started" and head(tree) == data.get("before"):
            pass
        else:
            raise Held("interrupted prepare needs reconciliation; not replaying")
    else:
        if receipt_path.parent.exists():
            for previous in receipt_path.parent.glob(card + "-*.json"):
                prior = json.loads(previous.read_text(encoding="utf-8"))
                if prior.get("phase") not in ("prepared", "prepare-conflict"):
                    raise Held("earlier prepare needs reconciliation; not starting another")
        registered(live, tree, f"worker/{card}")
        data = dict(request=request_id, phase="prepare-started",
                    before=head(tree), main=out(live, "rev-parse", "refs/heads/main"))
        write_receipt(receipt_path, data)
    checkpoint_receiver(tree, card, receipt_path, data, report)
    if admit is not None:
        admit()
    main = data["main"]
    data.update(phase="prepare-merging", checkpoint_head=head(tree))
    write_receipt(receipt_path, data)
    result = git(tree, "merge", "--no-ff", "-m",
                 f"Merge main into worker/{card} (house prepare)", main, check=False)
    conflicts = out(tree, "diff", "--name-only", "--diff-filter=U").splitlines()
    if result.returncode and not conflicts:
        # Keep all evidence. Do not abort a possibly interrupted operation.
        data.update(phase="prepare-unknown", error=(
            result.stderr or result.stdout).decode("utf-8", "replace")[-1000:])
        write_receipt(receipt_path, data)
        raise Held("prepare merge failed; inspect receipt before any retry")
    binary = [path for path in conflicts if any(
        b"\0" in git(tree, "show", f":{stage}:{path}", check=False).stdout
        for stage in (1, 2, 3))]
    if binary:
        # Same refusal policy as landing's merge: never stage an implicit
        # choice of a binary side. The checkpoint remains committed.
        git(tree, "merge", "--abort")
    data.update(phase="prepare-conflict" if conflicts else "prepared",
                after=head(tree), conflicts=conflicts,
                binary=binary, merge_aborted=bool(binary),
                changed=out(tree, "diff", "--name-only", data["checkpoint_head"], main).splitlines())
    write_receipt(receipt_path, data)
    return data


def receiver_paths(tree, names):
    """An ignored file is still someone's work; Git may otherwise overwrite it."""
    for name in names:
        p = tree / name
        for part in [p, *p.parents]:
            if part == tree:
                break
            if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
                raise Held("recipient has a linked path: " + name)
        if p.exists() and git(tree, "ls-files", "--error-unmatch", "--", name, check=False).returncode:
            raise Held("recipient has an untracked or ignored input: " + name)


def selected(root, paths):
    found = set()
    for name in paths:
        if name == "@preserved":
            # House-recorded source work, not a worker's cross-worktree read.
            # Deleted files are refused below, never propagated as deletions.
            changed = git(root, "diff", "--name-only", "-z", "HEAD").stdout
            new = git(root, "ls-files", "-z", "--others", "--exclude-standard").stdout
            found.update(p.decode("utf-8") for p in (changed + new).split(b"\0") if p and
                         not p.decode("utf-8").startswith("research/text-desk-lab/notation/sessions/"))
            continue
        name = safe_path(name.rstrip("/"))
        f = root / name
        if f.is_dir():
            if not name.startswith("research/"):
                raise Held("directory packages must be inside research/")
            names = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard",
                        "--", name + "/").stdout.split(b"\0")
            found.update(x.decode("utf-8") for x in names if x)
        else:
            found.add(name)
    if not found or len(found) > 200:
        raise Held("package must contain 1..200 files")
    manifest, size = {}, 0
    for name in sorted(found):
        safe_path(name)
        p = root / name
        # Reject symlinks/junctions anywhere, including intermediate directories.
        for part in [p, *p.parents]:
            if part == root:
                break
            if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
                raise Held("linked path is not transferable: " + name)
        if not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
            raise Held("missing or non-file input: " + name)
        if git(root, "check-ignore", "-q", "--", name, check=False).returncode == 0:
            raise Held("ignored input is not transferable: " + name)
        data = p.read_bytes()
        size += len(data)
        if size > 32 * 1024 * 1024:
            raise Held("package exceeds 32 MiB")
        manifest[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return manifest


def blob_manifest(root, commit, names):
    result = {}
    for name in names:
        data = git(root, "show", f"{commit}:{name}").stdout
        result[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return result


def transfer(landing, source, recipient, source_card, recipient_card, paths, receipt_path, key,
             report_checkpoint=None):
    """Both process leases and landing lock MUST already be held by the caller.

    A source snapshot is committed normally on its own worker branch, only when
    its index is empty. A projection commit includes ONLY selected paths on the
    common base. Merge-tree proves conflict freedom before receiver mutation.
    """
    live = landing.LIVE
    registered(live, recipient, "worker/" + recipient_card)
    data = {"request": key, "source": source_card, "recipient": recipient_card,
            "at": datetime.now(timezone.utc).isoformat()}
    if receipt_path.exists():
        old = read_receipt(receipt_path)
        if old.get("phase") in ("planned", "applied"):
            after = old["recipient_after"]
            if git(recipient, "merge-base", "--is-ancestor", after, "HEAD", check=False).returncode == 0:
                if old["phase"] == "planned":
                    old["received_files"] = blob_manifest(recipient, after, old["files"])
                    old["received_worktree_files"] = selected(recipient, list(old["files"]))
                    old["reconciled_at"] = datetime.now(timezone.utc).isoformat()
                old["phase"] = "applied"
                write_receipt(receipt_path, old)
                return old
            raise Held("previous transfer is not reconciled; do not replay it")
        if old.get("phase") == "preserving":
            raise Held("source preservation was interrupted; inspect its receipt before a new request")
        if old.get("phase") == "receiver-preserving":
            raise Held("recipient checkpoint was interrupted; inspect its receipt before a new request")
        if old.get("receiver_checkpoint"):
            data["receiver_checkpoint"] = old["receiver_checkpoint"]
    if source_card != "main":
        registered(live, source, "worker/" + source_card)
        if git(source, "diff", "--cached", "--name-only").stdout:
            raise Held("source has staged edits; not changing its index")
    # Validate source selection before changing the receiver's branch.
    manifest = selected(source, paths)
    checkpoint_receiver(recipient, recipient_card, receipt_path, data, report_checkpoint)
    source_before, before = head(source), head(recipient)
    receiver_paths(recipient, manifest)
    data.update(source_before=source_before, recipient_before=before,
                files=manifest, phase="preserving")
    write_receipt(receipt_path, data)
    if source_card == "main":
        try:
            branch = landing.hand([source / p for p in manifest], who="house-brings",
                                  words=f"preserved for {recipient_card}; receipt {key}\n\n" +
                                  json.dumps(manifest, sort_keys=True))
            saved = out(live, "rev-parse", branch)
        except ValueError as exc:
            if "nothing to land" not in str(exc):
                raise
            branch, saved = "main", source_before
    else:
        # Normal commit keeps this branch's worktree/index coherent. Other dirty
        # paths stay untouched. No hooks, models or imported package code run.
        git(source, "add", "-A", "--", *manifest)
        if git(source, "diff", "--cached", "--name-only").stdout:
            git(source, "commit", "-m", f"preserved by house for {recipient_card}; receipt {key}\n\n" +
                json.dumps(manifest, sort_keys=True))
        branch, saved = "worker/" + source_card, head(source)
    data.update(source_branch=branch, source_commit=saved, phase="preserved",
                committed_files=blob_manifest(source, saved, manifest))
    write_receipt(receipt_path, data)
    # Raw file hashes and Git blob hashes are both kept: Git's ordinary CRLF
    # conversion may differ; neither is silently labelled the other.
    if selected(source, list(manifest)) != manifest:
        raise Held("source changed while being preserved; receiver untouched")
    base = out(recipient, "merge-base", before, source_before)
    index = receipt_path.with_suffix(".index")
    env = {"GIT_INDEX_FILE": str(index)}
    try:
        git(recipient, "read-tree", base, env=env)
        for name in manifest:
            entry = out(source, "ls-tree", "-z", saved, "--", name).split("\t")[0].split()
            if len(entry) != 3 or entry[0] not in ("100644", "100755"):
                raise Held("unsupported source entry: " + name)
            git(recipient, "update-index", "--add", "--cacheinfo", entry[0], entry[2], name, env=env)
        tree = out(recipient, "write-tree", env=env)
        projection = out(recipient, "commit-tree", tree, "-p", base, "-m",
                         f"bring {source_card} to {recipient_card}\n\nreceipt {key}\n" +
                         json.dumps(data["committed_files"], sort_keys=True))
        # Only selected paths differ from the common base: unrelated source
        # commits (including held deployments) are not imported.
        merged = git(recipient, "merge-tree", "--write-tree", before, projection, check=False)
        if merged.returncode:
            data.update(phase="conflict", detail="selected source files conflict with recipient")
            write_receipt(receipt_path, data)
            raise Held(data["detail"])
        merged_tree = merged.stdout.decode().splitlines()[0]
        after = out(recipient, "commit-tree", merged_tree, "-p", before, "-p", projection,
                    "-m", f"house bring {source_card} to {recipient_card}; receipt {key}")
        if head(recipient) != before or head(source) != (source_before if source_card == "main" else saved):
            raise Held("branch moved during preparation; recipient untouched")
        clean_receiver(recipient)
        receiver_paths(recipient, manifest)
        # Durable plan precedes the ONLY receiver mutation. A crash afterward is
        # reconciled by ancestry, never by replaying source preservation.
        data.update(phase="planned", projection=projection, recipient_after=after)
        write_receipt(receipt_path, data)
        git(recipient, "merge", "--ff-only", "--no-overwrite-ignore", after)
        data["phase"] = "applied"
        data["received_files"] = blob_manifest(recipient, after, manifest)
        data["received_worktree_files"] = selected(recipient, list(manifest))
        write_receipt(receipt_path, data)
        return data
    finally:
        index.unlink(missing_ok=True)
