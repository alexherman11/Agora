"""Private test scratch cleanup, never process discovery or ACL repair."""
import os
import shutil
import stat
import time
import uuid
from pathlib import Path


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
