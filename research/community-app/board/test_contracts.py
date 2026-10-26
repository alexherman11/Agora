"""Adversarial boundaries beyond the realistic proof. Scratch only."""
import base64
import importlib.util
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path[:0] = [str(LAB), str(HERE)]
from kernel.kernel import Kernel, Refused
from kernel.blobs import receive, sniff, served, get


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', dict(tag='bc', name='Boundary checks',
        steward=dict(account='alex', name='Alex'), invites_counted_by='kernel', invites=[dict(code='x', uses=5)]))
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    return k, a, b


def act(k, a, text):
    out = k.run(a, text)
    assert out['ok'], out
    return out


def test_nested_word_limits_count_all_steps_and_undo(world):
    k, a, b = world
    entry = k.find_entry('post')
    act(k, a, 'look ' + entry)
    act(k, a, 'word-set ' + entry + ' once="at most 2 per day per person"')
    act(k, a, 'verb two steps="post One; post Two" help="two posts" may=members')
    out = act(k, b, 'two')
    assert not k.run(b, 'post Third')['ok']
    act(k, b, 'undo ' + out['records'][-1])
    act(k, b, 'post Now possible')
    before = len(k.log.records)
    assert not k.run(b, 'two')['ok']  # first step would reach two; second must refuse the whole act
    assert len(k.log.records) == before
    act(k, b, 'make kind=post sees=me text="Compatible private draft"')
    assert not k.run(b, 'make kind=post text="Cannot bypass slow posting"')['ok']


def test_upload_size_word_limit_and_facts_cannot_be_forged(world):
    k, a, b = world
    setting = act(k, a, 'make kind=file-settings max_bytes=12')['made'][0]
    assert not k.run(b, 'make kind=file-settings max_bytes=900000')['ok']
    assert not k.run(b, 'set ' + setting + ' max_bytes=900000')['ok']
    with pytest.raises(Refused):
        receive(k, b, b'x' * 13)
    assert not list((k.dir / 'blobs').glob('*'))
    entry = k.find_entry('upload')
    act(k, a, 'look ' + entry)
    act(k, a, 'word-set ' + entry + ' once="at most 1 per day per person"')
    first = receive(k, b, b'Hello', 'spoof.png')
    t = first['made'][0]
    assert k.state.get(t, 'mime_type') == 'text/plain'
    assert not receive(k, b, b'Too many')['ok']
    assert not k.run(b, 'upload name=without-bytes')['ok']
    assert not k.run(b, 'post text=x blob_hash=forged')['ok']
    assert not k.run(b, 'make kind=document visibility_of=' + t)['ok']
    act(k, b, 'undo ' + first['records'][-1])
    assert k.shown(b.person, t) is None
    assert receive(k, b, b'Again')['ok']


def test_file_attachment_visibility_tracks_parent_and_undo(world):
    k, a, b = world
    parent = act(k, a, 'make kind=note text=private sees=me')['made'][0]
    uploaded = receive(k, a, b'Attachment text', 'private.html')['made'][0]
    assert k.shown(b.person, uploaded) is None
    act(k, a, 'look ' + parent)
    act(k, a, 'look ' + uploaded)
    attached = act(k, a, 'attach ' + uploaded + ' to=' + parent)
    assert k.shown(b.person, uploaded) is None
    child = act(k, a, 'make kind=document within=' + uploaded)['made'][0]
    assert k.shown(b.person, child) is None
    hide = act(k, a, 'forget ' + parent + ' reason="Under review"')
    with pytest.raises(Refused):
        served(k, a.person, uploaded)
    assert k.shown(a.person, child) is None
    act(k, a, 'undo ' + hide['records'][-1])
    assert served(k, a.person, uploaded)[0] == b'Attachment text'
    assert k.shown(a.person, child)
    act(k, a, 'undo ' + attached['records'][-1])
    assert not k.state.get(uploaded, 'attached_to')
    assert k.shown(b.person, uploaded) is None


def test_pin_and_poll_deadlines_use_aware_dates(world):
    k, a, b = world
    k.clock = lambda: datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    t = act(k, a, 'post text=Deadline options="yes no" closes="2026-11-01T08:00:00-04:00"')['made'][0]
    act(k, a, 'look ' + t)
    act(k, a, 'pin ' + t + ' until=2026-11-01T12:00:00Z')
    assert not k.shown(b.person, t).get('pinned')
    assert not k.run(b, 'vote ' + t + ' yes')['ok']


def test_sniffing_and_orientation_strip_every_metadata_block(tmp_path):
    spec = importlib.util.spec_from_file_location('board_files_converter', HERE / 'files.py')
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    from PIL import Image
    image = Image.new('RGB', (40, 20), 'red')
    exif = Image.Exif()
    exif[274] = 6
    exif[271] = 'A camera'
    out = io.BytesIO()
    image.save(out, format='JPEG', exif=exif)
    result = converter.convert(out.getvalue(), sniff(out.getvalue()), tmp_path)
    holder = type('World', (), {'dir': tmp_path})()
    cleaned = Image.open(io.BytesIO(get(holder, result['clean'])))
    assert cleaned.size == (20, 40)
    assert (result['width'], result['height']) == cleaned.size
    assert not cleaned.getexif() and not cleaned.info
    assert sniff(b'<svg><script>alert(1)</script></svg>') == 'image/svg+xml'
    assert sniff(b'MZ\x00binary.exe') == 'application/octet-stream'


def test_hidden_bridge_upload_needs_grant_and_revocation_takes_effect(tmp_path):
    desktop = HERE.parents[1] / 'window-lab/kernel-desktop'
    sys.path.insert(0, str(desktop))
    from test_kdesk import Desk, quoted
    from widget_browser import Browser
    # This is the existing headless desktop fixture: OS windows are memory-only,
    # and the browser is a separate --headless process. The live desktop is never addressed.
    d = Desk()
    try:
        m = d.say('make kind=widget name=upload-proof code=' + quoted('await agora.ready;document.body.textContent="Upload proof";'))['made'][0]
        d.say('look ' + m)
        assert d.say('widget ' + m + ' grants="window.surface describe"')['ok']
        upload_grant = d.say('grant ' + m + ' words=upload')
        assert upload_grant['ok']
        sys.path.insert(0, str(LAB / 'widgets'))
        # Load only the existing frame evaluation helper, not its proof main.
        spec = importlib.util.spec_from_file_location('widget_proof_helpers', LAB / 'widgets/proof.py')
        helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helpers)
        with Browser(d.url) as c:
            from urllib.parse import quote
            c.call('Page.navigate', url=d.url + '/dev/signin?token=' + d.entry.token('alex') + '&next=' +
                   quote('/desk/widget.html?widget=' + m, safe=''))
            c.until('!!document.querySelector("#widget-surface iframe")')
            # Exercise the actual Blob API, postMessage, guarded broker, word
            # grant and content-addressed receipt, including the >100 KB path.
            result = helpers.inside(c, 'agora.upload(new File(["x".repeat(120000)], "photo.png")).then(r=>({ok:r.ok,id:r.made[0]}))')
            assert result['ok']
            assert d.k.state.get(result['id'], 'byte_size') == 120000
            assert d.k.state.get(result['id'], 'mime_type') == 'text/plain'
            assert d.k.log.records[-1]['by'] == m
            # Revoke only the upload grant, leaving the instance otherwise on.
            assert d.say('undo ' + upload_grant['records'][-1])['ok']
            denied = helpers.inside(c, 'agora.upload(new File(["no"], "denied.txt")).then(()=>false,e=>e.message.includes("grant"))')
            assert denied
    finally:
        d.close()


def test_model_photo_context_uses_clean_thumbnail_and_labels_suggestion(tmp_path):
    from unittest.mock import patch
    from kernel.blobs import put
    spec = importlib.util.spec_from_file_location('board_model_contract', LAB / 'modules/model/model.py')
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    from PIL import Image
    image = io.BytesIO()
    Image.new('RGB', (8, 8), 'blue').save(image, 'PNG')
    data = image.getvalue()
    root = tmp_path / 'world'
    digest = put(root, data)
    home = root / 'modules/model'
    home.mkdir(parents=True)
    message = dict(use='photo', word='model.ask', caller=dict(person='bc2', name='Alex'),
                   args=dict(words='Suggest alt text', kv=dict(about='bc20')))
    with patch.object(model, 'home', home), patch.object(model, 'limit'), patch.object(model, 'context',
            return_value=[dict(id='bc20', kind='photo')]), patch.object(model, 'read', side_effect=[[], [dict(thumbnail=digest)]]), patch.object(
            model, 'generate', return_value='A blue square.') as generate:
        result = model.plan(message)
        assert 'suggested photo description' in result['text']
        assert base64.b64decode(generate.call_args.kwargs['images'][0]) == data
