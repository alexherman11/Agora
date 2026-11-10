"""media_links: which files on this PC the desk may show as pictures and films, and how a path written in words names
one (a5941, 16 Oct 2026; Alex: 'can we get that video to be hyperlinked in chat and open in a native window here').

A line of talk links a film simply by holding its path, as text: src/desktop/demos/a5820/writing-demo.mp4,
C:/Projects/Agora4/src/desktop/demos/a5820/writing-demo.mp4 or a backslashed one. A text that says `media`
(scene.py) asks find() which paths in its words are media the desk may show; the painter draws those, and deskd serves
them at /media/<folder>/<path> (serve() below), checking every request again here. Everything else stays words.

The folders the desk may show (FOLDERS), and nothing outside them, ever:
    demos   src/desktop/demos    the films and shots builders make (screen_tools.py, film.py)
    media   media/                       anything else a person puts there to show (both are ignored by git)
In a worker's worktree (.worktrees/<name>) each folder is looked for there first and then in the main checkout, where
those files really are (screen_tools.py writes demos/ there). Kinds: KINDS. No svg (a drawing can carry script), no
folder listings, no file names outside the kinds, no '..', no link that leads out of its folder (resolved first).
"""
import mimetypes
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FOLDERS = {"demos": Path("src/desktop/demos"), "media": Path("media")}
KINDS = {".mp4": "video", ".webm": "video", ".m4v": "video",
         ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image", ".webp": "image"}
TYPES = {".mp4": "video/mp4", ".m4v": "video/mp4", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
CHUNK = 4 << 20                 # an open range is answered with at most this much; the browser asks for the rest

# a path in words: an optional drive, then names joined by / or \, ending in a kind. Spaces end a path (quote-free
# words); a name with spaces in it is not found (say so where it matters: a5941's done note)
_PATH = re.compile(r"(?<![\w/\\.:-])((?:[A-Za-z]:[\\/])?(?:[\w.-]+[\\/])+[\w.-]+\.(?:" +
                   "|".join(k[1:] for k in KINDS) + r"))(?![\w/\\-])", re.I)


def roots(repo=None):
    """-> [(folder name, absolute directory)], each folder in this checkout first, then in the main one."""
    repo = Path(repo) if repo else REPO
    bases = [repo] + ([repo.parent.parent] if repo.parent.name == ".worktrees" else [])
    return [(name, (b / rel).resolve()) for name, rel in FOLDERS.items() for b in bases]


def _inside(p, d):
    try:
        p.relative_to(d)
        return True
    except ValueError:
        return False


def resolve(path, repo=None):
    """A path as written (relative to the checkout, or absolute) -> (folder, rel posix path, absolute file), or a
    refusal string saying why it is not shown. Relative paths are read from each checkout in turn."""
    s = str(path).strip().replace("\\", "/")
    ext = os.path.splitext(s)[1].lower()
    if ext not in KINDS:
        return f"{path!r} is not a picture or film the desk shows ({', '.join(KINDS)})"
    if any(part == ".." for part in s.split("/")):
        return f"{path!r} climbs out with '..'"
    rs = roots(repo)
    if re.match(r"[A-Za-z]:/|/", s):
        tries = [Path(s)]
    else:
        bases = list(dict.fromkeys(d.parents[len(FOLDERS[n].parts) - 1] for n, d in rs))   # the checkouts themselves
        tries = [b / s for b in bases]
    for t in tries:
        try:
            f = t.resolve()
        except OSError:
            continue
        for name, d in rs:
            if _inside(f, d) and f.is_file():
                return name, f.relative_to(d).as_posix(), f
    if not any(_inside(Path(os.path.abspath(t)), d) for t in tries for _n, d in rs):
        return f"{path!r} is outside the folders the desk may show ({', '.join(r.as_posix() for r in FOLDERS.values())})"
    return f"{path!r}: no such file"


def find(text, repo=None):
    """The media a text's words name, in order, each file once however it was spelled: {path (as first written), src
    (/media/...), kind, name}; and the paths that look like media but are not shown, each {path, refused}."""
    out, seen = [], set()
    for m in _PATH.finditer(text or ""):
        p = m.group(1)
        r = resolve(p, repo)
        key = p if isinstance(r, str) else f"/media/{r[0]}/{r[1]}"
        if key in seen:
            continue
        seen.add(key)
        if isinstance(r, str):
            out.append({"path": p, "refused": r})
        else:
            folder, rel, f = r
            out.append({"path": p, "src": key, "kind": KINDS[f.suffix.lower()], "name": f.name})
    return out


def file_for(url_path, repo=None):
    """/media/<folder>/<rel> -> the absolute file, or a refusal string. The URL is never trusted: the same checks as a
    path in words, against the named folder only."""
    from urllib.parse import unquote
    rest = unquote(url_path)[len("/media/"):]
    folder, _, rel = rest.partition("/")
    if folder not in FOLDERS or not rel:
        return f"no media folder {folder!r} (folders: {', '.join(FOLDERS)})"
    if "\\" in rel or any(part in ("..", "") for part in rel.split("/")) or re.match(r"[A-Za-z]:", rel):
        return f"{rel!r} is not a plain path inside {folder}"
    if os.path.splitext(rel)[1].lower() not in KINDS:
        return f"{rel!r} is not a picture or film the desk shows"
    for name, d in roots(repo):
        if name != folder:
            continue
        f = (d / rel).resolve()
        if _inside(f, d) and f.is_file():
            return f
    return f"{folder}/{rel}: no such file"


def serve(handler, url_path, repo=None):
    """Answer a GET for /media/... on a BaseHTTPRequestHandler: the file, or the asked range of it (206), so a film
    seeks. 403 for anything not shown, 416 for a range past the end."""
    f = file_for(url_path, repo)
    if isinstance(f, str):
        body = f.encode("utf-8")
        handler.send_response(404 if f.endswith("no such file") else 403)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        return
    size = f.stat().st_size
    start, end, partial = 0, size - 1, False
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", (handler.headers.get("Range") or "").strip())
    if m and (m.group(1) or m.group(2)):
        partial = True
        if m.group(1):
            start = int(m.group(1))
            end = min(int(m.group(2)), size - 1) if m.group(2) else min(size - 1, start + CHUNK - 1)
        else:                                   # bytes=-N: the last N
            start, end = max(0, size - int(m.group(2))), size - 1
        if start >= size or start > end:
            handler.send_response(416)
            handler.send_header("Content-Range", f"bytes */{size}")
            handler.send_header("Content-Length", "0")
            handler.end_headers()
            return
    handler.send_response(206 if partial else 200)
    handler.send_header("Content-Type", TYPES.get(f.suffix.lower()) or mimetypes.guess_type(f.name)[0] or "application/octet-stream")
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("X-Content-Type-Options", "nosniff")
    if partial:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.send_header("Content-Length", str(end - start + 1))
    handler.end_headers()
    with open(f, "rb") as fh:
        fh.seek(start)
        left = end - start + 1
        while left > 0:
            chunk = fh.read(min(left, 1 << 16))
            if not chunk:
                break
            handler.wfile.write(chunk)
            left -= len(chunk)
