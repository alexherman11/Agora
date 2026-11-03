"""Two weeks of council organising, on a disposable HTTP kernel. No windows.

People and messages are imagined; every printed check/count/time is ran.
Original camera JPEG fixtures are fetched once, stored here with provenance.
The actual local model process is used for one requested summary; --model
requires inference success rather than accepting its explicit offline message.
"""
import argparse
import csv
import io
import json
import secrets
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import wave
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path[:0] = [str(HERE), str(LAB), str(LAB / 'tests')]
from install import install, modules
from protocol import line, quote
from kernel.kernel import Kernel
from kernel.door import serve
from kernel import scratch
from test_skeleton import StandInEntry, post


def pdf():
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    for n, text in enumerate(['Council vote on 4 November. Neighbours request a continuance.',
            'The staff report proposes 120 homes and a public walking route.',
            'Please submit written comments before the council meeting.'], 1):
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'),
                                 NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 40 720 Td (Page {n}: {text}) Tj ET'.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def fixtures():
    doc = io.BytesIO()
    with zipfile.ZipFile(doc, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Letter to the council: please preserve the walking route.</w:t></w:r></w:p></w:body></w:document>')
    audio = io.BytesIO()
    with wave.open(audio, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b'\x00\x00' * 16000)
    table = io.StringIO()
    csv.writer(table).writerows([['Name', 'Street', 'Signed']] + [[f'Neighbour {i:02}', f'{i} Seabright', 'yes'] for i in range(1, 41)])
    return {'planning.pdf': pdf(), 'camera.txt': (HERE / 'fixtures/gps-camera-photo.jpg').read_bytes(),
            'gps-edge.jpg': (HERE / 'fixtures/gps-photo.jpg').read_bytes(),
            'signatures.csv': table.getvalue().encode(), 'letter.docx': doc.getvalue(),
            'meeting.ics': b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:council@seabright\r\nSUMMARY:Council meeting\r\nDTSTART:20261104T190000Z\r\nDTEND:20261104T210000Z\r\nLOCATION:City Hall\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n',
            'notes.md': b'# Route notes\nKeep a safe walking route.', 'notes.txt': b'Bring flyers and a pen.',
            'meeting.wav': audio.getvalue(), 'active.jpg': b'<html><script>alert(1)</script></html>',
            'vector.svg': b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            'broken.pdf': b'%PDF-1.7\nthis is not a complete PDF', 'unknown.bin': b'\x00\xff\x12unknown'}


class Proof:
    def __init__(self, model=False):
        self.tmp = scratch.TemporaryDirectory(prefix='agora-board-proof-', ignore_cleanup_errors=True)
        self.entry = StandInEntry(secrets.token_hex(16))
        self.k = Kernel(self.tmp.name, dict(tag='bd', name='Seabright board proof',
            steward=dict(account='alex', name='Alex'), invites_counted_by='kernel',
            invites=[dict(code='board-proof', uses=40)], modules=modules()))
        self.at = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        self.k.clock = lambda: self.at
        self.srv, self.host = serve(self.k, self.entry.url, self.entry.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.entry.kernel_url = self.url = 'http://127.0.0.1:' + str(self.srv.server_address[1])
        self.entry.sessions['alex'] = dict(account='alex', method='proof')
        self.tokens = {'Alex': 'alex'}
        self.people = {'Alex': self.k.accounts['alex']}
        self.checks = 0
        self.model = model
        for name in ('board', 'files'):
            assert self.host.wait_offered(self.k.module_named(name)), name

    def check(self, text, condition, detail=''):
        self.checks += 1
        print(f'{self.checks:02} {"ok" if condition else "FAIL"} {text}' + (' · ' + str(detail) if detail else ''), flush=True)
        assert condition, text

    def raw(self, who, text, mode='do'):
        code, receipt = post(self.url + '/' + mode, dict(line=text), token=self.tokens[who])
        assert code == 200, (code, receipt)
        return receipt

    def say(self, who, text):
        r = self.raw(who, text)
        assert r['ok'], (who, text, r['text'])
        return r

    def see(self, who, text):
        r = self.raw(who, text, 'see')
        assert r['ok'], (who, text, r['text'])
        return r

    def upload(self, who, name, data, group=None, token=True, origin=None):
        headers = {'Content-Type': 'application/octet-stream', 'X-Filename': name}
        if token:
            headers['Authorization'] = 'Bearer ' + self.tokens[who]
        if origin:
            headers['Origin'] = origin
        req = urllib.request.Request(self.url + '/upload' + ('?in=' + group if group else ''), data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def file(self, who, target, query=''):
        req = urllib.request.Request(self.url + '/files/' + target + query,
            headers={'Authorization': 'Bearer ' + self.tokens[who]})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def join(self, name):
        token, said = self.entry.sign_in(name, name, invite='board-proof')
        assert token, said
        self.tokens[name], self.people[name] = token, said['person']

    def run(self):
        ids = install(lambda s: self.say('Alex', s), lambda s: self.see('Alex', s))
        ch = ids['channels']
        self.join('Maya')
        neighbours = [f'Neighbour {i:02}' for i in range(1, 31)]
        for name in neighbours:
            self.join(name)
        for gid in ch.values():
            self.say('Alex', line('role', self.people['Maya']) + ' leader in=' + gid)
        self.check('30 neighbours and 2 leaders joined', len(self.people) == 32)
        self.check('all words have help', all(r.get('help') for r in self.see('Alex', 'rows word')['rows']))
        first = neighbours[0]
        self.say(first, 'board.seen')
        self.at += timedelta(hours=1)
        question = self.say(first, line('board.post', text='How do we speak at the council vote?',
            post_kind='question', **{'in': ch['Neighbours']}))['made'][0]
        reply = self.say(neighbours[1], line('board.reply', question, text='Sign up at City Hall before 7 pm.'))
        second = self.say(neighbours[2], line('board.reply', reply['made'][0], text='I can help with signup.'))
        refused = self.raw(neighbours[3], line('board.reply', second['made'][0], text='Too deep'))
        self.check('two-level replies enforced', not refused['ok'])
        answered = self.say(first, line('board.answer', question, reply=reply['made'][0]))
        self.check('asker marks answer', any(r['id'] == question for r in self.see(first, 'catch-up')['rows'] if r['category'] == 'answer'))
        self.say(first, 'undo ' + answered['records'][-1])
        self.check('answer undo restores needs answers', any(r['id'] == question for r in self.see(first, 'needs-answers')['rows']))
        self.say('Maya', line('board.answer', question, reply=reply['made'][0]))
        event = self.say('Maya', line('board.post', post_kind='event', title='Council vote', text='Meet at City Hall',
            start='2026-11-04T19:00:00Z', end='2026-11-04T21:00:00Z', location='City Hall', seats='40',
            **{'in': ch['Meetings & events']}))['made'][0]
        poll = self.say('Maya', line('board.post', post_kind='poll', text='Request a continuance?', options='yes no abstain',
            closes='2026-11-03T18:00:00Z', **{'in': ch['Neighbours']}))['made'][0]
        ask = self.say(first, line('board.post', post_kind='ask', text='Need three flyer volunteers', seats='3',
            **{'in': ch['Asks & offers']}))['made'][0]
        self.say(neighbours[1], line('board.post', post_kind='offer', text='I can print forty flyers', seats='1',
            **{'in': ch['Asks & offers']}))
        document = self.say(first, line('board.post', post_kind='document', text='The planning documents',
            **{'in': ch['Research & documents']}))['made'][0]

        data = fixtures()
        self.check('unauthenticated upload refused', self.upload(first, 'x', b'test', token=False)[0] == 401)
        self.check('cross-site upload refused', self.upload(first, 'x', b'test', origin='https://elsewhere.invalid')[0] == 403)
        uploads, rich, conversions = {}, {}, {}
        for name, content in data.items():
            code, r = self.upload(first, name, content, ch['Research & documents'])
            assert code == 200 and r['ok'], r
            uploads[name] = r['made'][0]
            conversion = r.get('conversion')
            assert conversion and conversion['ok'], conversion
            conversions[name] = conversion
            if len(conversion['made']):
                rich[name] = conversion['made'][0]
            self.see(first, 'look ' + uploads[name])
            self.see(first, 'look ' + document)
            self.say(first, line('attach', uploads[name], to=document))
        from PIL import Image
        source = Image.open(io.BytesIO(data['camera.txt']))
        gps = source.getexif().get_ifd(34853)
        photo = self.see(first, 'file-read ' + rich['camera.txt'])['rows'][0]
        code, headers, clean = self.file(neighbours[1], uploads['camera.txt'])
        cleaned = Image.open(io.BytesIO(clean))
        thumb = Image.open(io.BytesIO(self.file(first, rich['camera.txt'], '?variant=thumbnail')[2]))
        self.check('real camera photo GPS removed from served image and thumbnail',
            bool(gps.get(2)) and bool(gps.get(4)) and not cleaned.getexif() and not thumb.getexif(),
            f'{len(gps)} original GPS tags; {len(cleaned.getexif())} cleaned EXIF tags; {source.width}x{source.height}')
        self.check('photo metadata and thumbnail dimensions', photo['width'] == source.width and max(thumb.size) <= 360)
        self.check('served files have nosniff and sandbox CSP', headers.get('X-Content-Type-Options') == 'nosniff' and
            'sandbox' in headers.get('Content-Security-Policy', '') and headers['Content-Type'] == 'image/png')
        pdf = self.see(first, 'file-read ' + rich['planning.pdf'])['rows'][0]
        self.check('real generated PDF has three extracted pages', pdf['page_count'] == 3 and '120 homes' in pdf['pages'][1], pdf['preview_status'])
        self.check('PDF searchable by page', any(r.get('page') == 2 for r in self.see(neighbours[1], 'board.search q="120 homes"')['rows']))
        hidden_document = self.say(neighbours[1], line('board.personal', document, action='hide'))
        self.check('personal hide also removes attached document search results only for that reader',
            not self.see(neighbours[1], 'board.search q="120 homes"')['rows'] and
            bool(self.see(first, 'board.search q="120 homes"')['rows']))
        self.say(neighbours[1], 'undo ' + hidden_document['records'][-1])
        quoted = self.say(neighbours[1], line('board.reply', document, text='The walking route matters.',
            source=rich['planning.pdf'], page='2', quote='120 homes and a public walking route'))
        self.check('PDF page passage quoted in a reply', bool(quoted['records']))
        self.check('false quote refused', not self.raw(neighbours[1], line('board.reply', document, text='Fake quote',
            source=rich['planning.pdf'], page='2', quote='not in this document'))['ok'])
        table = self.see(first, 'file-read ' + rich['signatures.csv'])['rows'][0]
        self.check('CSV is a table of forty signatures', len(table['rows']) == 40 and len(table['columns']) == 3)
        self.check('DOCX, TXT and Markdown are documents', all(n in rich for n in ('letter.docx', 'notes.txt', 'notes.md')))
        self.say(first, 'undo ' + conversions['notes.txt']['records'][-1])
        self.check('conversion undo leaves the original file and removes richer data',
            self.k.shown(self.people[first], uploads['notes.txt']) is not None and
            self.k.shown(self.people[first], rich['notes.txt']) is None)
        self.say(first, 'files.convert ' + uploads['notes.txt'])
        self.check('WAV duration measured', self.see(first, 'file-read ' + rich['meeting.wav'])['rows'][0]['duration'] == 2.0)
        self.check('ICS becomes an event and exports a calendar', rich['meeting.ics'] in self.k.things('event') and
            'DTSTART:20261104T190000Z' in self.see(first, 'board.calendar ' + rich['meeting.ics'])['text'])
        for name in ('active.jpg', 'vector.svg', 'unknown.bin'):
            code, h, _ = self.file(first, uploads[name])
            self.check(name + ' only downloads despite its filename', code == 200 and h['Content-Disposition'].startswith('attachment'))
        self.check('broken conversion stays a plain file with reason', 'reason' in self.see(first, 'file-read ' + uploads['broken.pdf'])['rows'][0])
        self.check('file identity cannot be forged', not self.raw(first, line('set', uploads['planning.pdf'], blob_hash='0' * 64))['ok'] and
                   not self.raw(first, line('make', kind='file', mime_type='image/png'))['ok'])
        # Prove originals/extracted pages never enter the append-only log.
        logged = json.dumps(self.k.log.records)
        self.check('file bytes and extracted pages stay out of the log', 'The staff report proposes 120 homes' not in logged and
            data['camera.txt'].hex() not in logged and 'blob_hash' in logged)

        for i, who in enumerate(neighbours):
            self.say(who, line('board.rsvp', event, status='maybe' if i % 4 == 0 else 'going'))
            self.say(who, 'vote ' + poll + (' yes' if i % 3 else ' no'))
            self.say(who, 'like ' + question)
        poll_row = next(p for p in self.see(first, 'rows post')['rows'] if p['id'] == poll)
        self.check('30 RSVPs, 30 sealed votes, 30 sealed upvotes',
            self.k.shown(self.people[first], event)['claims'] == 30 and poll_row['votes'] == 30 and
            self.k.shown(self.people[first], question)['likes'] == 30)
        self.check('vote and like history is sealed', all(r['by'] == 'sealed' and not r['facts'] for r in
            self.see(first, 'history ' + poll)['rows'] if r['sealed']))
        claim = self.say(first, 'claim ' + ask)
        self.say(neighbours[1], 'claim ' + ask)
        self.say(neighbours[2], 'claim ' + ask)
        self.check('flyer slots close when full', not self.raw(neighbours[3], 'claim ' + ask)['ok'])
        self.say(first, 'undo ' + claim['records'][-1])
        self.check('claim undo reopens a seat', self.k.shown(self.people[first], ask)['seats_left'] == 1)
        self.say(neighbours[3], 'claim ' + ask)

        announcement = self.say('Maya', line('board.post', text='Council vote is next week', post_kind='announcement',
            **{'in': ch['Announcements']}))['made'][0]
        self.see('Maya', 'look ' + announcement)
        self.say('Maya', line('pin', announcement, until='2026-10-24T12:00:00Z'))
        self.see('Maya', 'look ' + question)
        hidden = self.say('Maya', line('forget', question, reason='Checking the meeting time with the clerk'))
        self.check('leader hide leaves visible reason and hides replies', 'Checking the meeting time' in self.see(first, 'forgotten')['text'] and
            self.k.shown(self.people[first], reply['made'][0]) is None)
        self.say('Maya', 'undo ' + hidden['records'][-1])
        self.check('leader undo restores thread and replies', self.k.shown(self.people[first], reply['made'][0]) is not None)
        self.say('Maya', line('board.decide', question, text='We will speak at the 4 November council meeting.'))
        self.check('leader outcome appears in catch-up', any(r.get('category') == 'decision' for r in self.see(first, 'catch-up')['rows']))
        self.check('neighbour cannot decide or post announcements', not self.raw(first, line('board.decide', question, text='I decide'))['ok'] and
            not self.raw(first, line('board.post', text='Unofficial', post_kind='announcement', **{'in': ch['Announcements']}))['ok'])

        personal = self.say(first, line('board.personal', question, action='hide'))
        self.check('personal hide affects only its reader', question not in {r['id'] for r in self.see(first, 'board.feed')['rows']} and
            question in {r['id'] for r in self.see(neighbours[1], 'board.feed')['rows']})
        self.say(first, 'undo ' + personal['records'][-1])
        for action in ('bookmark', 'follow', 'mute'):
            mark = self.say(first, line('board.personal', question, action=action))
            if action == 'mute':
                self.say(first, 'undo ' + mark['records'][-1])
        self.check('bookmarks read back', question in {r['id'] for r in self.see(first, 'board.feed order=bookmarks')['rows']})
        self.say(neighbours[1], line('board.report', question, reason='Please verify the signup time'))
        self.check('reports visible only to leaders', len(self.see('Maya', 'board.queue')['rows']) == 1 and not self.see(first, 'board.queue')['rows'])

        private = self.say('Alex', line('group', name='Private organisers'))['made'][0]
        self.say('Alex', line('role', self.people[first]) + ' member in=' + private)
        self.say('Alex', line('make', kind='board-channel', group=private, title='Private organisers'))
        # Private group also gets the same explicit dictionary controls.
        base = self.k.find_entry('post')
        local = self.say('Alex', line('dictionary-copy', base, word='reply', **{'in': private}))['made'][0]
        self.see('Alex', 'look ' + local)
        self.say('Alex', line('word-set', local, once='at most 30 per day per person'))
        secret = self.say(first, line('board.post', text='PRIVATE-COUNCIL-SENTINEL', **{'in': private}))['made'][0]
        _, secret_upload = self.upload(first, 'private.txt', b'PRIVATE-DOCUMENT-SENTINEL', private)
        sf = secret_upload['made'][0]
        self.see(first, 'look ' + sf)
        self.see(first, 'look ' + secret)
        self.say(first, line('attach', sf, to=secret))
        for text in ('board.search q=SENTINEL', 'catch-up', 'rows file', 'rows document'):
            reading = self.see(neighbours[1], text)
            self.check('private group absent from ' + text, 'SENTINEL' not in json.dumps(reading) and sf not in {r.get('id') for r in reading['rows']})
        self.check('private file URL refuses outsiders', self.file(neighbours[1], sf)[0] == 404 and self.file(first, sf)[0] == 200)
        self.check('no raw CAS URL', self.file(first, self.k.state.get(sf, 'blob_hash'))[0] == 404)
        self.say('Alex', line('role', self.people[neighbours[1]]) + ' member in=' + private)
        self.check('private-group member is a positive visibility control',
            bool(self.see(neighbours[1], 'board.search q=SENTINEL')['rows']) and self.file(neighbours[1], sf)[0] == 200)
        self.say('Alex', line('role', self.people[neighbours[1]]) + ' none in=' + private)
        self.check('membership revocation closes search and file access again',
            not self.see(neighbours[1], 'board.search q=SENTINEL')['rows'] and self.file(neighbours[1], sf)[0] == 404)

        lost = self.say(neighbours[2], line('make', kind='kind', name='Lost pet', fields='pet_name last_seen', required='pet_name'))
        pet = self.say(neighbours[2], line('board.post', post_kind='Lost pet', text='Has anyone seen Pip?', pet_name='Pip',
            last_seen='Murray Street', **{'in': ch['Neighbours']}))
        self.check('neighbour adds Lost pet with words alone', bool(pet['made']) and bool(lost['made']))
        # Two weeks: every channel carries a post and replies. Announcements are
        # posted by its two leaders; all thirty neighbours may reply there.
        self.at = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
        for day in range(13):
            self.at = datetime(2026, 10, 23, 12, tzinfo=timezone.utc) + timedelta(days=day)
            for i in range(24):
                channel = list(ch)[i % 6]
                who = ('Alex' if i % 2 else 'Maya') if channel == 'Announcements' else neighbours[(day * 7 + i) % 30]
                p = self.say(who, line('board.post', text=f'Day {day + 2}: council organising update {i + 1}',
                    post_kind='announcement' if channel == 'Announcements' else 'discussion', **{'in': ch[channel]}))['made'][0]
                if i % 4 == 0:
                    self.say(neighbours[(day + i) % 30], line('board.reply', p, text='Thanks. I can help before the vote.'))
                if i % 3 == 0:
                    self.say(neighbours[(day + i + 1) % 30], 'like ' + p)
        # Add a new followed reply after the last-seen point.
        self.say(neighbours[4], line('board.reply', question, text='The clerk confirmed the signup time today.'))
        self.check('pin expires at until', not self.k.shown(self.people[first], announcement).get('pinned'))
        self.check('poll refuses votes after closing time', not self.raw('Alex', 'vote ' + poll + ' yes')['ok'])
        self.check('followed replies are in catch-up', any(r['category'] == 'following' for r in self.see(first, 'catch-up')['rows']))
        self.at = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
        loud = neighbours[-1]
        for i in range(5):
            self.say(loud, line('board.post', text='PLEASE READ THIS ' + str(i), **{'in': ch['Neighbours']}))
        slowed = self.raw(loud, line('board.post', text='AND ONE MORE', **{'in': ch['Neighbours']}))
        self.check('all-caps poster hits polite dictionary slow limit', not slowed['ok'] and 'most' in slowed['text'], slowed['text'])
        local_post = self.k.find_entry('post', ch['Neighbours'])
        self.see('Maya', 'look ' + local_post)
        changed = self.say('Maya', line('word-set', local_post, once='at most 6 per day per person'))
        self.say(loud, line('board.post', text='Thank you; one final detail.', **{'in': ch['Neighbours']}))
        self.check('leader changes channel slow rule with words', bool(changed['records']))
        self.see(loud, 'rows post')
        editable = pet['made'][0]
        self.see(neighbours[2], 'look ' + editable)
        edit = self.say(neighbours[2], line('set', editable, text='Pip is home safely. Thank you.'))
        self.check('module-made post belongs to its human for editing', bool(edit['records']) and len(self.see(first, 'history ' + editable)['rows']) >= 2)
        self.say(neighbours[2], 'undo ' + edit['records'][-1])
        self.check('post edit undo restores text', 'Has anyone seen Pip?' == self.k.state.get(editable, 'text'))
        self.model_proof(first)
        timings = {}
        for text in ('board.feed', 'catch-up', 'board.search q=council'):
            elapsed = []
            for who in neighbours:
                start = time.perf_counter()
                self.see(who, text)
                elapsed.append((time.perf_counter() - start) * 1000)
            timings[text] = dict(median_ms=round(statistics.median(elapsed), 2), max_ms=round(max(elapsed), 2))
        count = len(self.k.things('post'))
        self.check('realistic two-week post count', 380 <= count <= 430, count)
        self.check('orderings and why-here return plain data', 'why_here' in self.see(first, 'new')['rows'][0] and bool(self.see(first, 'board.why-here ' + question)['rows']))
        seen_before = self.see(first, 'catch-up')['rows']
        seen = self.say(first, 'board.seen')
        self.check('mark seen clears catch-up', bool(seen_before) and not self.see(first, 'catch-up')['rows'])
        self.say(first, 'undo ' + seen['records'][-1])
        self.check('undo seen restores catch-up', bool(self.see(first, 'catch-up')['rows']))
        self.check('agent badges label the person', any(r['name'] == 'agent for ' + first for r in self.see(first, 'board.badges')['rows']))
        self.check('scratch log replay retains the exact world', Kernel(self.tmp.name).state.snapshot() == self.k.state.snapshot())
        result = dict(checks=self.checks, people=32, posts=count, replies=sum(bool(self.k.state.get(t, 'reply_to')) for t in self.k.things('post')),
                      days=14, timings=timings, pdf_preview=pdf['preview_status'], model=self.model_result,
                      model_attempts=self.model_attempts,
                      live_desktop_touched=False)
        print('BOARD PROOF ' + json.dumps(result, sort_keys=True), flush=True)
        return result

    def model_proof(self, first):
        token, _ = self.entry.sign_in(first, first, agent='Council helper')
        self.tokens['Agent'] = token
        caught = self.see('Agent', 'catch-up')
        self.check('agent reads same personal catch-up', caught['rows'] == self.see(first, 'catch-up')['rows'])
        context = self.say('Agent', line('make', kind='board-catch-up', sees='me',
            title='Catch-up summary context', text=json.dumps(caught['rows'], ensure_ascii=False)))['made'][0]
        run = [sys.executable, str(LAB / 'modules/model/model.py')]
        self.say('Alex', line('module model', run=json.dumps(run), grants='rows look'))
        assert self.host.wait_offered(self.k.module_named('model'))
        for e in self.see('Alex', 'rows word')['rows']:
            if e.get('from') == 'module:model':
                self.see('Alex', 'look ' + e['id'])
                self.say('Alex', line('word-set', e['id'], may='members'))
        summary = self.see('Agent', line('model.ask ' + quote('Summarise the council catch-up in two short sentences.'), about=context))
        # Cold loading can outlast the existing model module's seven-second
        # request timeout. Retry only when status confirms a running backend;
        # never restart/download or count an offline message as a real summary.
        self.model_attempts = 1
        while self.model and 'local model ·' not in summary['text'] and self.model_attempts < 3:
            status = self.see('Agent', 'model.status')
            if not status['rows'] or not status['rows'][0].get('up'):
                break
            self.model_attempts += 1
            summary = self.see('Agent', line('model.ask ' + quote('Summarise the council catch-up in two short sentences.'), about=context))
        self.model_result = summary['text']
        self.check('model.ask returns labelled summary or explicit offline state', 'local model' in summary['text'], summary['text'][:220])
        if self.model:
            self.check('requested real model summary completed', 'local model ·' in summary['text'])

    def close(self):
        self.host.stop_all()
        self.srv.shutdown()
        self.srv.server_close()
        self.entry.srv.shutdown()
        self.entry.srv.server_close()
        self.tmp.cleanup()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=HERE / 'evidence.json')
    ap.add_argument('--model', action='store_true', help='require a labelled real local-model summary')
    args = ap.parse_args()
    proof = Proof(model=args.model)
    try:
        result = proof.run()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    finally:
        proof.close()


if __name__ == '__main__':
    main()
