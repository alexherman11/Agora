"""Reviewed conversion process; no network, no executable upload handling.

Original/derived bytes live only in the kernel CAS. No lasting private database.
Bounds on decompression, image pixels, pages and extracted text keep malformed
uploads from monopolising this board. A conversion exception is a file result.
"""
import csv
import io
import json
import sys
import warnings
import wave
import zipfile
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'agora'
sys.path.insert(0, str(LAB))
from kernel.blobs import get, put
from protocol import line, read, run
from documents import ENTRIES as DOCUMENT_WORDS, call as document_call

world = None
MAX_TEXT = 2_000_000
MAX_PIXELS = 24_000_000


def convert(data, mime, root):
    if mime.startswith('image/') and mime != 'image/svg+xml':
        from PIL import Image, ImageOps
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('photo exceeds 24 million pixels')
                # Apply orientation before stripping all source info, including
                # EXIF GPS, ICC/XMP, comments and PNG text chunks.
                oriented = ImageOps.exif_transpose(source)
                mode = 'RGBA' if 'A' in oriented.getbands() or 'transparency' in source.info else 'RGB'
                image = Image.new(mode, oriented.size)
                image.paste(oriented.convert(mode))
                width, height = image.size
                out = io.BytesIO()
                image.save(out, format='PNG')
                clean = put(root, out.getvalue())
                image.thumbnail((360, 360))
                out = io.BytesIO()
                image.save(out, format='PNG')
                return dict(kind='photo', width=width, height=height,
                            clean=clean, thumbnail=put(root, out.getvalue()), alt='',
                            metadata='EXIF, GPS, XMP and camera metadata stripped; first frame only')
    if mime == 'application/pdf':
        from pypdf import PdfReader
        doc = PdfReader(io.BytesIO(data))
        if doc.is_encrypted:
            raise ValueError('encrypted PDF; upload an unlocked copy')
        if len(doc.pages) > 300:
            raise ValueError('PDF exceeds 300 pages')
        pages, count = [], 0
        for page in doc.pages:
            if len(page.get_contents().get_data() if page.get_contents() else b'') > 8 * 1024 * 1024:
                raise ValueError('PDF page stream exceeds extraction budget')
            text = page.extract_text() or ''
            count += len(text)
            if count > MAX_TEXT:
                raise ValueError('PDF text exceeds extraction budget')
            pages.append(text)
        result = dict(kind='document', page_count=len(pages), pages=pages, preview_status='no installed PDF renderer')
        try:
            import fitz
        except ImportError:
            return result
        with fitz.open(stream=data, filetype='pdf') as rendered:
            if rendered.page_count:
                page = rendered[0]
                scale = min(1, 800 / max(page.rect.width, page.rect.height))
                result['preview'] = put(root, page.get_pixmap(matrix=fitz.Matrix(scale, scale)).tobytes('png'))
                result['preview_status'] = 'first page rendered with installed PyMuPDF'
        return result
    if mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            item = z.getinfo('word/document.xml')
            if item.file_size > 8 * 1024 * 1024:
                raise ValueError('DOCX XML exceeds 8 MB')
            raw = z.read(item)
            if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
                raise ValueError('DOCX entities are not accepted')
            tree = ElementTree.fromstring(raw)
            ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            text = '\n'.join(''.join(n.itertext()) for n in tree.iter(ns + 'p'))
            if len(text) > MAX_TEXT:
                raise ValueError('DOCX text exceeds extraction budget')
            return dict(kind='document', pages=[text], page_count=1, pagination='logical text, no Word pagination')
    if mime == 'text/csv':
        rows = list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
        if len(rows) > 20_001 or len(rows[0]) > 200:
            raise ValueError('table exceeds 20,000 rows or 200 columns')
        if any(len(r) != len(rows[0]) for r in rows):
            raise ValueError('CSV has inconsistent columns')
        return dict(kind='table', columns=rows[0], rows=rows[1:], row_count=len(rows) - 1)
    if mime == 'text/calendar':
        text = data.decode('utf-8-sig').replace('\r\n ', '').replace('\r\n\t', '')
        if text.count('BEGIN:VEVENT') != 1:
            raise ValueError('calendar upload needs exactly one VEVENT')
        facts = {}
        for raw in text.splitlines():
            key, sep, value = raw.partition(':')
            if sep:
                name = key.split(';')[0]
                if name in ('SUMMARY', 'DTSTART', 'DTEND', 'LOCATION', 'UID', 'DESCRIPTION'):
                    if 'TZID=' in key:
                        raise ValueError('timezone-specific ICS is not supported; use UTC or an all-day date')
                    facts[name] = value.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
        if not facts.get('DTSTART'):
            raise ValueError('calendar event has no start')
        from datetime import datetime
        def date(v):
            fmt = '%Y%m%d' if len(v) == 8 else '%Y%m%dT%H%M%SZ'
            return datetime.strptime(v, fmt).strftime('%Y-%m-%d' if len(v) == 8 else '%Y-%m-%dT%H:%M:%SZ')
        return dict(kind='event', title=facts.get('SUMMARY', 'Meeting'), start=date(facts['DTSTART']),
                    end=date(facts['DTEND']) if facts.get('DTEND') else '', location=facts.get('LOCATION', ''),
                    description=facts.get('DESCRIPTION', ''), uid=facts.get('UID', ''))
    if mime.startswith(('audio/', 'video/')):
        duration = None
        if mime == 'audio/wav':
            with wave.open(io.BytesIO(data)) as media:
                duration = media.getnframes() / media.getframerate()
        return dict(kind='media', media_type=mime, duration=duration)
    if mime == 'text/plain':
        text = data.decode('utf-8-sig')
        if len(text) > MAX_TEXT:
            raise ValueError('text exceeds extraction budget')
        return dict(kind='document', pages=[text], page_count=1)
    return dict(kind='file', reason='unsupported or active content; download only')


def start(message):
    global world
    world = Path(message['home']).parents[1]


def call(message):
    if message['word'] != 'files.convert':
        return document_call(message, read)
    use = message['use']
    args = message.get('args') or {}
    target = args.get('target')
    files = read(use, 'rows file')
    file = next((r for r in files if r['id'] == target), None)
    if not file:
        raise ValueError('no visible uploaded file')
    if file.get('file_result'):
        raise ValueError('already converted; undo its conversion before converting again')
    # Kernel get checks the digest; the process reads only a file already admitted
    # through its caller's ordinary visibility and grant checks.
    holder = type('World', (), {'dir': world})()
    try:
        result = convert(get(holder, file['blob_hash']), file['mime_type'], world)
    except Exception as exc:
        result = dict(kind='file', reason=type(exc).__name__ + ': ' + str(exc)[:400])
    raw = json.dumps(result, ensure_ascii=False).encode()
    if len(raw) > 16 * 1024 * 1024:
        result = dict(kind='file', reason='converted result exceeds 16 MB')
        raw = json.dumps(result).encode()
    digest = put(world, raw)
    return dict(lines=[line('file-result', target, manifest=digest)], saw={target: file['rev']})


if __name__ == '__main__':
    run(DOCUMENT_WORDS + [dict(word='files.convert', kind='do', takes='<id>', may='members', undo='yes',
              help='files.convert <upload>: convert one visible file. Metadata-free photo, PDF pages, DOCX/text, CSV table, UTC calendar event, or media. Failures remain plain files with a reason. Undo removes conversion; off stops the process.')],
        call, 'Converting visible uploads; bounded extraction, no network, content-addressed output', start)
