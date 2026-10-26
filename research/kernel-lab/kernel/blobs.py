"""Content addressed attachments. Bytes cross the door, never the act log.

The converter is a reviewed process, not an OS sandbox. Its published facts
are admitted by file-result; originals and derivatives are always addressed by
their actual digest. No URL accepts a path or a bare digest as authority.
"""
import hashlib
import io
import json
import re
import secrets
import zipfile
from pathlib import Path

from .kernel import Refused

DEFAULT_CAP = 25 * 1024 * 1024
PROTECTED = {'blob_hash', 'byte_size', 'mime_type', 'file_source', 'file_result',
             'attached_to', 'visibility_of', 'upload_owner'}


def sniff(data):
    """Conservative bytes-only classification; active/unknown content downloads."""
    if data.startswith(b'%PDF-'):
        return 'application/pdf'
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
        return 'audio/wav'
    if data[:3] == b'ID3' or data[:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
        return 'audio/mpeg'
    if data[:4] == b'OggS':
        return 'audio/ogg'
    if len(data) > 12 and data[4:8] == b'ftyp':
        if data[8:12] in (b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1', b'avif'):
            return 'image/heic' if data[8:12] != b'avif' else 'image/avif'
        return 'video/mp4'
    if data.startswith(b'\x1aE\xdf\xa3'):
        return 'video/webm'
    if data[:2] == b'PK':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if '[Content_Types].xml' in z.namelist() and 'word/document.xml' in z.namelist():
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        except (ValueError, zipfile.BadZipFile):
            pass
        return 'application/zip'
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError:
        return 'application/octet-stream'
    if '\x00' in text or any(ord(c) < 32 and c not in '\t\r\n' for c in text):
        return 'application/octet-stream'
    lower = text.lstrip().lower()
    if '<svg' in lower[:4096]:
        return 'image/svg+xml'
    if re.search(r'<(?:!doctype\s+html|html|script|iframe|body)\b', lower[:4096]):
        return 'text/html'
    if text.lstrip().startswith('BEGIN:VCALENDAR'):
        return 'text/calendar'
    import csv
    try:
        rows = list(csv.reader(io.StringIO(text[:65536])))
        if len(rows) > 1 and len(rows[0]) > 1 and all(len(r) == len(rows[0]) for r in rows[:20]):
            return 'text/csv'
    except csv.Error:
        pass
    return 'text/plain'  # Markdown is plain text; filenames never confer authority.


def cap(k):
    settings = [k.state.things[t] for t in k.things('file-settings')]
    try:
        value = int(settings[0].get('max_bytes', DEFAULT_CAP)) if settings else DEFAULT_CAP
    except (ValueError, TypeError):
        raise Refused('the steward must repair file-settings.max_bytes')
    if not 0 < value <= 1024 * 1024 * 1024:
        raise Refused('file size setting must be from 1 byte to 1 GB')
    return value


def put(k_or_dir, data):
    root = Path(k_or_dir.dir if hasattr(k_or_dir, 'dir') else k_or_dir) / 'blobs'
    root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    dest = root / digest
    if not dest.exists():
        tmp = root / ('upload-' + secrets.token_hex(12))
        tmp.write_bytes(data)
        tmp.replace(dest)
    return digest


def get(k, digest):
    if not re.fullmatch('[0-9a-f]{64}', str(digest)):
        raise Refused('invalid blob address')
    try:
        data = (k.dir / 'blobs' / digest).read_bytes()
    except OSError as exc:
        raise Refused('file bytes are unavailable') from exc
    if hashlib.sha256(data).hexdigest() != digest:
        raise Refused('file integrity check failed')
    return data


def receive(k, actor, data, name='Upload', group=None):
    """One request, one ordinary dictionary act; no reusable staging capability."""
    if len(data) > cap(k):
        raise Refused('That file is too large. Please choose a smaller file or ask a steward.')
    import shlex
    line = 'upload name=' + shlex.quote(str(name).replace('\\', '/').rsplit('/', 1)[-1][:200])
    if group:
        line += ' in=' + shlex.quote(group)
    # Check authority before storing bytes. Rechecked under the ordinary act lock.
    with k.lock:
        eid = k.find_entry('upload', group)
        if not eid or not k.may(actor, k.entry(eid), None, group or k.place):
            raise Refused('you have no grant to upload here')
    previous = getattr(k._local, 'upload_bytes', None)
    k._local.upload_bytes = data
    try:
        out = k.run(actor, line)
        if out.get('ok') and out.get('made') and k.find_entry('files.convert'):
            conversion = k.run(actor, 'files.convert ' + out['made'][0])
            out['conversion'] = conversion
        return out
    finally:
        k._local.upload_bytes = previous


def upload(k, actor, st, entry, tx, group, saw=None):
    data = getattr(k._local, 'upload_bytes', None)
    if data is None:
        raise Refused('upload needs file bytes through the upload door or agora.upload(file)')
    if len(data) > cap(k):
        raise Refused('That file is too large. Please choose a smaller file or ask a steward.')
    t = tx.mint()
    facts = dict(kind='file', name=st.kv.get('name', 'Upload'), blob_hash=put(k, data),
                 byte_size=len(data), mime_type=sniff(data), upload_owner=actor.person,
                 made_by=actor.id, sees='person:' + actor.person)
    if actor.id != actor.person:
        facts['for'] = actor.person
    for a, v in facts.items():
        tx.set(t, a, v)
    tx.set(t, 'in:' + group, len(k.log.records) + 1)
    return dict(text='ok upload ' + t + ' [r?] · private until attached')


def attach(k, actor, st, entry, tx, group, saw=None):
    t, parent = st.target, st.kv.get('to')
    a = k.shown(actor.person, parent)
    if k.state.get(t, 'kind') != 'file' or a is None or parent == t:
        raise Refused('attach <file> to=<visible thing>')
    owner = k.state.get(t, 'upload_owner')
    if owner != actor.person and not k.is_leader(actor.person, group):
        raise Refused('only the uploader or its leaders attach a file')
    if a.get('made_by') not in (actor.id, actor.person) and a.get('for') != actor.person and not any(
            k.is_leader(actor.person, g) for g in k.groups_of(parent)):
        raise Refused('attach to your own thing, or a thing you lead')
    # Never publish someone else's private file by attaching it to a wider post.
    if owner != actor.person:
        raise Refused('the uploader chooses where their file is shared')
    k.fence(actor, t, ['attached_to'], saw)
    k.fence(actor, parent, [], saw)
    tx.set(t, 'attached_to', parent)
    tx.set(t, 'visibility_of', parent)
    tx.set(t, 'sees', 'place')
    # Moving between parents is explicit, fenced and undoable; all derivatives
    # point to the file and follow its current permission.
    return dict(text='ok attach [r?] · follows who may see its parent')


def file_result(k, actor, st, entry, tx, group, saw=None):
    """Only the granted files process can attest derived bytes; callers cannot."""
    if actor.kind != 'module' or k.state.get(actor.module, 'name') != 'files':
        raise Refused('only the granted files converter publishes file results')
    t = st.target
    if k.state.get(t, 'kind') != 'file':
        raise Refused('file-result needs an uploaded file')
    k.fence(actor, t, ['file_result'], saw)
    digest = st.kv.get('manifest')
    raw = get(k, digest)
    if len(raw) > 16 * 1024 * 1024:
        raise Refused('converted content is too large')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise Refused('invalid conversion manifest') from exc
    kind = result.get('kind')
    if kind not in {'file', 'photo', 'document', 'table', 'event', 'media'}:
        raise Refused('unsupported converted kind')
    for key in ('clean', 'thumbnail', 'preview'):
        if result.get(key):
            get(k, result[key])
    if kind == 'photo':
        from PIL import Image
        if not result.get('clean') or not result.get('thumbnail'):
            raise Refused('a photo needs cleaned and thumbnail bytes')
        for key in ('clean', 'thumbnail'):
            with Image.open(io.BytesIO(get(k, result[key]))) as image:
                if image.format != 'PNG' or image.getexif() or image.info.get('exif'):
                    raise Refused('a cleaned photo must be a metadata-free PNG')
    tx.set(t, 'file_result', digest)
    if kind == 'file':
        return dict(text='ok file-result [r?] · plain file: ' + str(result.get('reason', 'download only')))
    rich = tx.mint()
    for a, v in dict(kind=kind, file_source=t, visibility_of=t, made_by=actor.id,
                     name=k.state.get(t, 'name'), file_result=digest).items():
        tx.set(rich, a, v)
    if actor.person != actor.id:
        tx.set(rich, 'for', actor.person)
    tx.set(rich, 'in:' + group, len(k.log.records) + 1)
    # Only small structural facts go in the log. Text, rows and image pixels
    # stay in the manifest blob and are read through file-read.
    for key in ('width', 'height', 'page_count', 'duration', 'start', 'end', 'location', 'title'):
        if key in result:
            tx.set(rich, key, result[key])
    if kind == 'photo':
        tx.set(rich, 'alt', '')
    if kind == 'event':
        tx.set(rich, 'seats', str(result.get('seats', 200)))
    return dict(text='ok file-result ' + rich + ' [r?] · ' + kind)


def manifest(k, reader, t):
    a = k.shown(reader, t)
    if a is None:
        raise k.no_such(t)
    if not a.get('file_result'):
        return a, {'kind': 'file', 'reason': 'not converted yet'}
    return a, json.loads(get(k, a['file_result']))


def file_read(k, actor, st, entry, tx, group, saw=None):
    a, result = manifest(k, actor.person, st.target)
    k.mark(actor, st.target, a)
    page = st.kv.get('page')
    if page is not None:
        try:
            n = int(page)
            if n < 1:
                raise ValueError()
            text = result['pages'][n - 1]
        except (ValueError, KeyError, IndexError):
            raise Refused('choose a page from 1 to the document page count')
        return dict(text=text, rows=[dict(id=st.target, page=n, text=text)])
    return dict(text=json.dumps(result, ensure_ascii=False), rows=[dict(result, id=st.target)])


def served(k, reader, t, variant='content'):
    a, result = manifest(k, reader, t)
    source = k.state.things.get(a.get('file_source') or t, {})
    mime = source.get('mime_type', 'application/octet-stream')
    digest = source.get('blob_hash')
    disposition = 'attachment'
    if mime.startswith('image/') and mime != 'image/svg+xml':
        # Original photo bytes are never served, even with download=1.
        digest = result.get('thumbnail' if variant == 'thumbnail' else 'clean')
        if not digest:
            raise Refused('the cleaned photo is not available yet')
        mime, disposition = 'image/png', 'inline'
    elif mime.startswith(('audio/', 'video/')):
        disposition = 'inline'
    elif mime == 'application/pdf':
        disposition = 'attachment'
    # Force all text/HTML/SVG and unknown content to download. No sniffing by
    # browser, plugins, uploaded paths, or raw CAS route.
    data = get(k, digest)
    name = re.sub(r'[^a-zA-Z0-9 ._-]', '_', str(source.get('name') or 'download'))[:160]
    if mime == 'image/png':
        name = Path(name).stem + '.png'
    return data, mime, [('X-Content-Type-Options', 'nosniff'),
        ('Content-Security-Policy', "sandbox; default-src 'none'; base-uri 'none'; form-action 'none'"),
        ('Content-Disposition', disposition + '; filename="' + name + '"'),
        ('Cache-Control', 'private, no-store')]
