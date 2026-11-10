"""Hidden fixture integration for House review. Never targets the live desktop."""
import json
import time
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / 'agora')]
from painter.fixture import Fixture
from painter.browser import Page
from install import install, modules
from protocol import line
from documents_install import PARTS, install_documents, templates
from painter.install import upsert, Q
from kernel.inpage import Principal
from kernel.blobs import receive


def scoped_fixture_provider(d, library):
    """Private fixture only; never changes the live module's held authority."""
    provider = d.rows('module', name='files')[0]['id']
    d.say(line('grant', provider, words='make set',
               only='kind:document-folder,document-entry;library:' + library))


def test_published_document_word_arguments():
    """Exercise kernel admission and the real files host, not direct call()."""
    f = Fixture()
    try:
        d = f.door
        spec = next(s for s in modules() if s['name'] == 'files')
        d.say(line('module ' + spec['name'], run=json.dumps(spec['run']),
                   publishes=spec['publishes'], grants=spec['grants']))
        assert f.d.host.wait_offered(f.k.module_named(spec['name'])), spec['name']
        group = d.say('group name=Documents-arguments open=yes')['made'][0]
        library = d.say(line('make', kind='document-library', name='arguments',
                             **{'in': group}))['made'][0]
        scoped_fixture_provider(d, library)
        reading = d.request('/see', dict(line='files.browse library=' + library))
        assert reading['ok'] and reading['rows'] == [], reading
        folder = d.say(line('files.folder', name='Notes', library=library))['made'][0]
        session = f.d.entry.check(f.token)
        viewer = f.k.actor_for(f.k.accounts[session['account']])
        uploaded = receive(f.k, viewer, b'Published argument proof', 'proof.txt', group)
        assert uploaded['ok'], uploaded
        entry = d.say(line('files.store', uploaded['made'][0], library=library,
                           parent=folder))['made'][0]
        d.say(line('files.rename', entry, name='Evidence'))
        d.say(line('files.move', entry, to=library))
        reading = d.request('/see', dict(line='files.browse library=' + library))
        assert reading['ok'], reading
        stored = next(r for r in reading['rows'] if r['id'] == entry)
        assert stored['name'] == 'Evidence' and stored['parent'] == library, stored
        # Named libraries still pass through the module's viewer-visible
        # library lookup; removing the accidental target must not bypass it.
        for text in ('files.browse', 'files.browse library=' + folder):
            refused = d.request('/see', dict(line=text))
            assert not refused['ok'] and 'visible inherited library' in refused['text'], refused
        for text in ('files.store library=' + library,
                     'files.rename name=Missing', 'files.move to=' + library):
            refused = d.request('/do', dict(line=text))
            assert not refused['ok'] and 'needs a thing' in refused['text'], refused
    finally:
        f.close()


def test_real_drop_picker_preview_and_nested_library():
    f = Fixture()
    page = None
    try:
        d = f.door
        # As in proof.Proof, publish both modules before install() stores
        # verbs that refer to board.feed and board.catch-up.
        for spec in modules():
            d.say(line('module ' + spec['name'], run=json.dumps(spec['run']),
                       publishes=spec['publishes'], grants=spec['grants']))
            assert f.d.host.wait_offered(f.k.module_named(spec['name'])), spec['name']
        install(d.say, lambda text: d.request('/see', dict(line=text)))
        ids = install_documents(d)
        scoped_fixture_provider(d, ids['library'])
        # Diagnose setup before opening Chromium, under the widget's actual
        # narrowed authority rather than the steward's unrestricted door.
        # Resolve the same existing session as Page, following the door's
        # account-to-person mapping; "alex" is a signer, not an account key.
        session = f.d.entry.check(f.token)
        assert session and not session.get('agent'), 'Expected the fixture person session'
        viewer = f.k.actor_for(f.k.accounts[session['account']])
        principal = Principal(f.k, ids['widget'], viewer, 'documents-ui-readiness')
        try:
            installed = {c['name'] for c in d.rows('component')}
            assert not (set(PARTS) | {'file', 'table'}) - installed, installed
            compiled = principal.run('look-view ' + ids['lens'] + ' plan=yes', mode='see')
            assert compiled['ok'], compiled
            initial = compiled['rows'][0]
            for name in ('document-library', 'document-toolbar', 'document-upload', 'document-list'):
                assert initial['counts'].get(name) == 1, initial
            stopped = [p for p in initial['parts']
                       if p['health']['health'] == 'stopped' or p['health'].get('quarantined')]
            assert not stopped, stopped
            assert all(c['trusted'] for c in initial['components']), initial['components']
            browsing = principal.run('files.browse library=' + ids['library'], mode='see')
            assert browsing['ok'], browsing
            # painter.js awaits these subscriptions before its first refresh.
            # Use the broker's own authority predicate; never grant around it.
            missing = [word for word in ('make', 'set', 'forget', 'undo', 'component', 'component-action')
                       if not principal.hears(word)]
            assert not missing, (
                'Documents painter cannot reach its first render; missing widget authority: '
                + ' '.join('hear:' + word for word in missing)
                + '. No grants were added; coordinator authorization is required.'
            )
        finally:
            principal.close()
        page = Page(f.url, f.token, ids['widget'])
        page.until('!!document.querySelector(".document-upload input[type=file]")')
        page.js('document.querySelector(".document-toolbar input").value="Meeting notes";[...document.querySelectorAll(".document-folder-form button")].pop().click()')
        # Pump the page while waiting: the hidden browser adds the widget-host header by pausing each request, and
        # paused requests only continue while this test is talking to the browser (widget_browser.py Fetch.requestPaused).
        page.until('(()=>!!document.querySelector(".document-entry"))()')
        assert any(r.get('name') == 'Meeting notes' for r in d.rows('document-folder'))
        page.until('[...document.querySelectorAll(".document-entry>button")].some(b=>b.textContent.includes("Meeting notes"))')
        page.js('[...document.querySelectorAll(".document-entry>button")].find(b=>b.textContent.includes("Meeting notes")).click()')
        page.until('document.querySelector(".document-toolbar nav").textContent.includes("Meeting notes")')
        # Real browser File bytes travel through the authenticated host upload door.
        page.js('(()=>{const data=new DataTransfer();data.items.add(new File(["Neighbour minutes"],"minutes.txt",{type:"text/plain"}));document.querySelector(".document-upload [data-part=drop]").dispatchEvent(new DragEvent("drop",{bubbles:true,cancelable:true,dataTransfer:data}))})()')
        page.until('[...document.querySelectorAll(".document-entry>button")].some(b=>b.textContent==="minutes.txt")')
        page.js('[...document.querySelectorAll(".document-entry>button")].find(b=>b.textContent==="minutes.txt").click()')
        page.until('document.querySelector(".nb-file")?.textContent.includes("Neighbour minutes")')
        page.js('(()=>{const data=new DataTransfer();data.items.add(new File(["Picker notes"],"picker.txt",{type:"text/plain"}));const input=document.querySelector(".document-upload input");input.files=data.files;input.dispatchEvent(new Event("change",{bubbles:true}))})()')
        page.until('[...document.querySelectorAll(".document-entry>button")].some(b=>b.textContent==="picker.txt")', 40)
        def attached():
            ids = {e['id'] for e in d.rows('document-entry')}
            return len(ids) == 2 and all(r.get('attached_to') in ids for r in d.rows('file'))
        for _ in range(60):        # pumping the page lets its paused attach requests continue
            if attached():
                break
            page.js('1')
            time.sleep(0.25)
        folders = d.rows('document-folder')
        folder = next(r for r in folders if r['name'] == 'Meeting notes')
        entries = d.rows('document-entry')
        assert len(entries) == 2 and all(r['parent'] == folder['id'] for r in entries)
        assert all(r.get('attached_to') in {e['id'] for e in entries} for r in d.rows('file'))
        # The same arrangement nests under another host with independent view state.
        host = upsert(d, 'lens', 'documents-host-test', painter='components',
                      text='root : column\n  documents : column, of tag:document-library, prop:name=seabright-documents as library, each documents-view\n' + templates(),
                      view=json.dumps(dict(documentsFolder=folder['id'], documentsOpen='')))
        plan = d.say('look-view ' + host + ' plan=yes')['rows'][0]
        assert plan['counts']['document-library'] == 1
        # plan=yes lists readings without running them, so check the host's own view reaches the listing,
        # and that listing (run as a reading) holds both files.
        listing = next(r['line'] for r in plan['readings'] if r['path'].endswith('/listing'))
        assert listing == f'files.browse library="{ids["library"]}" parent="{folder["id"]}"', listing
        browsed = d.request('/see', dict(line=listing))
        assert browsed['ok'] and sorted(r['name'] for r in browsed['rows']) == ['minutes.txt', 'picker.txt'], browsed
        assert not any(p['health']['health'] == 'stopped' for p in plan['parts'])
        d.say('personal-view seabright-documents documents-view.title="Our research"')
        d.say('personal-style seabright-documents target=document-entry padding="16px"')
        page.until('document.querySelector(".document-library h2")?.textContent==="Our research"')
        # The hidden browser blocks the live stream and favicon itself (net::ERR_BLOCKED_BY_CLIENT); only script
        # errors and non-network console errors count.
        errors = [e for e in page.errors if e['method'] == 'Runtime.exceptionThrown'
                  or e['params'].get('entry', {}).get('source') != 'network']
        assert not errors, errors
    finally:
        if page:
            page.close()
        f.close()
