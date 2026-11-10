"""Private test scratch cleanup, never process discovery or ACL repair."""

import gzip
import hashlib
import json
import os
import shutil
import stat
import sys
import time
import uuid
from pathlib import Path


def diagnostic(errors, directory):
    """Bound user-facing output; preserve every error in an immutable compressed receipt."""
    payload = json.dumps(list(errors), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"cleanup-{digest}.json.gz"
    packed = gzip.compress(payload, mtime=0)
    if target.exists():
        if hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() != digest:
            raise RuntimeError("existing cleanup evidence does not match its digest") from None
    else:
        # Publish only a complete, flushed receipt. An interrupted write must
        # never occupy the content-addressed final name with truncated data.
        pending = directory / (".cleanup-" + uuid.uuid4().hex + ".tmp")
        try:
            with pending.open("xb") as output:
                output.write(packed)
                output.flush()
                os.fsync(output.fileno())
            os.replace(pending, target)
        finally:
            try:
                pending.unlink(missing_ok=True)
            except OSError:
                pass  # A private .tmp can remain; it is never a published receipt.
    return {
        "error_count": len(errors),
        "errors": [str(e)[:360] for e in errors[:8]],
        "omitted": max(0, len(errors) - 8),
        "sha256": digest,
        "evidence": str(target),
    }


def diagnostic_text(receipt):
    return (
        f"{receipt['error_count']} cleanup errors; {receipt['omitted']} omitted here. "
        f"Full evidence: {receipt['evidence']}\n" + "\n".join(receipt["errors"])
    )


def cleanup_fixture(path):
    """For the caller's own private fixture only; no process termination or ACL changes."""
    errors = remove_tree(path, readonly=True)
    if errors:
        directory = Path(
            os.environ.get("AGORA_CLEANUP_REPORTS") or Path(path).parent / "cleanup-evidence"
        )
        try:
            print(
                "retained private fixture: " + diagnostic_text(diagnostic(errors, directory)),
                file=sys.stderr,
            )
        except (OSError, RuntimeError) as exc:
            print(
                f"retained private fixture: could not save {len(errors)} cleanup errors: {exc}",
                file=sys.stderr,
            )
        return False
    return True


def visit_directory():
    """Landing supplies an outside-room root; standalone tests use inherited TMP."""
    import tempfile

    root = Path(os.environ.get("AGORA_VISIT_TMP") or tempfile.gettempdir())
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("test-visit-" + uuid.uuid4().hex)
    # Inherit the directory ACL instead of mkdtemp's owner-only Windows mode.
    path.mkdir()
    return path


def remove_tree(path, attempts=20, pause=0.1, readonly=False):
    """Return remaining errors, retrying sharing races and accepting vanished paths.

    readonly is ONLY for repositories this test created: Git creates read-only
    objects. Clearing that file attribute does not change a security ACL.
    Never use it for the landing room's pre-existing leftovers.
    """
    path = Path(path)
    errors = []

    def failed(fn, name, exc_info):
        exc = exc_info[1]
        if isinstance(exc, FileNotFoundError):
            return
        if readonly and isinstance(exc, PermissionError) and Path(name).is_file():
            try:
                mode = os.stat(name).st_mode
                if not mode & stat.S_IWRITE:
                    os.chmod(name, mode | stat.S_IWRITE)
                    fn(name)
                    return
            except FileNotFoundError:
                return
            except OSError as retry:
                exc = retry
        errors.append(f"{name}: {type(exc).__name__}: {exc}")

    for attempt in range(attempts):
        errors = []
        try:
            shutil.rmtree(path, onerror=failed)
        except FileNotFoundError:
            return []
        except OSError as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
        if not path.exists():
            return []
        if attempt + 1 < attempts:
            time.sleep(pause)
    return errors or [f"{path}: still exists after {attempts} cleanup attempts"]
