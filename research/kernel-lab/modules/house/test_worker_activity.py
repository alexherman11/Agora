"""Synthetic provider streams through persisted activity; no real worker or window."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transport as T
import worker_activity as A
from test_builders import manager, state


@pytest.mark.parametrize('command,secret', [
    ('FOO=ordinary git status', 'ordinary'),
    ('export FOO="two words"; git status', 'two words'),
    ("$env:FOO = 'two words'; git status", 'two words'),
    ('set "FOO=two words" && git status', 'two words'),
    ('set FOO=two words && git status', 'two words'),
    ('setx FOO "two words"', 'two words'),
    ('curl --token "two words"', 'two words'),
    ('curl --password=private', 'private'),
    ('Invoke-WebRequest -Token private', 'private'),
    ('curl -H "Authorization: Bearer private" url', 'private'),
    ("curl -H 'Authorization: custom private' url", 'private'),
    ('curl https://alex:private@example.org', 'private'),
    ('curl https://example.org?token=private&ok=1', 'private'),
    ('curl -u alex:private url', 'private'),
    ('mysql -p private', 'private'),
    ('echo sk-fixturesecret123', 'sk-fixturesecret123'),
    ('echo ghp_fixturesecret123', 'ghp_fixturesecret123'),
    ('echo eyJfixture.payload.signature', 'eyJfixture.payload.signature'),
    ('python -c \'cfg={"password": "private"}\'', 'private'),
    ('KEY=private git status', 'private'),
    ('curl --token=private --password "two words"', 'private'),
    ('curl --token=private --password "two words"', 'two words'),
    ('python -c \'cfg={"token": "private"}\'', 'private'),
    ('python -c \'cfg={"key": "private"}\'', 'private'),
    (r'KEY="first \"private\" last" git status', 'private'),
    ('KEY="first `"private`" last" git status', 'private'),
    ("KEY='first ''private'' last' git status", 'private'),
])
def test_redacts_before_summary_and_detail(command, secret):
    safe = A.record('ran', command)
    assert secret not in json.dumps(safe)
    assert '[hidden]' in safe['detail']


def test_commands_paths_and_old_entries_survive_restart(manager):
    s = state(manager)
    commands = [
        {'type':'codex_event', 'method':'item/started',
         'data':{'item':{'type':'commandExecution', 'command':'git diff --check'}}},
        {'type':'codex_event', 'method':'item/completed',
         'data':{'item':{'type':'fileChange', 'changes':[{'path':'agora-wm/wm_module.py'}]}}},
        {'type':'assistant', 'message':{'content':[
            {'type':'tool_use', 'name':'Bash', 'input':{'command':'git status', 'description':'private input'}},
            {'type':'tool_use', 'name':'Write', 'input':{'file_path':'hello.py','content':'private content'}},
            {'type':'tool_use', 'name':'Edit', 'input':{'file_path':'other.py','new_string':'private content'}},
            {'type':'tool_use', 'name':'Read', 'input':{'file_path':'hello.py'}}]}},
    ]
    manager.event(s, 'act', 'commandExecution')  # historic entry, no invented details
    for raw in commands:
        for event in T.reduce(raw):
            safe = A.tool(event)
            manager.event(s, 'act', safe['summary'], safe['detail'])
    disk = (manager.home / s['run'] / 'state.json').read_text()
    assert 'private' not in disk
    s.update(json.loads(disk))
    log = manager.log(s['task'])
    assert 'ran: git diff --check' in log['text']
    assert 'changed: agora-wm/wm_module.py' in log['text']
    assert 'changed: hello.py' in log['text']
    assert 'changed: other.py' in log['text']
    assert 'read: hello.py' in log['text']
    assert s['activity'][0]['text'] == 'commandExecution'
    assert 'no saved command or paths' in log['text']
    assert 'act-detail\t' in log['rows'][0]['log']


def test_long_multiline_command_has_short_preview_and_full_sanitized_detail():
    command = 'git diff --check\n' + 'some-long-path/' * 30 + '\nTOKEN=private'
    event = T.reduce({'type':'codex_event', 'method':'item/started',
                      'data':{'item':{'type':'commandExecution','command':command}}})[0]
    safe = A.tool(event)
    assert len(safe['summary']) == 120
    assert '\n' not in safe['summary']
    assert safe['detail'] == 'ran: ' + command.replace('private', '[hidden]')
    assert event['input'] == {}


def test_unknown_tools_do_not_publish_arbitrary_inputs():
    assert A.tool({'name':'Unknown','input':{'command':'private'}}) is None
    assert T.reduce({'type':'codex_event','method':'item/completed',
                     'data':{'item':{'type':'reasoning','text':'private'}}}) == []
    assert T.reduce({'type':'codex_event','method':'item/started',
                     'data':{'item':{'type':'fileChange','changes':[]}}}) == []


@pytest.mark.parametrize('provider', ['codex', 'claude'])
def test_no_command_surface_contains_raw_values(manager, provider):
    s = state(manager)
    notifications = []
    manager.h.m.happen = lambda *args: notifications.append(args)
    command = 'KEY=envvalue curl --token tokenvalue --password "passwordvalue"'
    raw = ({'type':'codex_event', 'method':'item/started',
            'data':{'item':{'type':'commandExecution', 'command':command}}}
           if provider == 'codex' else
           {'type':'assistant', 'message':{'content':[
               {'type':'tool_use','name':'Bash','input':{'command':command}}]}})
    safe = A.tool(T.reduce(raw)[0])
    manager.event(s, 'act', safe['summary'], safe['detail'])
    surfaces = json.dumps({
        'state': s,
        'disk': (manager.home / s['run'] / 'state.json').read_text(),
        'log': manager.log(s['task']),  # text, console preview, and expanded JSON detail
        'notifications': notifications,
    })
    for secret in ('envvalue', 'tokenvalue', 'passwordvalue'):
        assert secret not in surfaces
