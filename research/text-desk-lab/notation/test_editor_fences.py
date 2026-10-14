"""A gesture may edit the other text it actually read, never its newer replacement."""

import importlib
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest


@pytest.fixture
def door(tmp_path, monkeypatch):
    argv = sys.argv
    try:
        sys.argv = ["deskd.py"]
        deskd = importlib.import_module("deskd")
    finally:
        sys.argv = argv
    monkeypatch.setattr(deskd, "SESSIONS", tmp_path)
    deskd._DESKS.clear()
    deskd._SCENES.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(line, actor="maker", observed=None):
        data = json.dumps(
            {"session": "editor-test", "as": actor, "line": line, "observed": observed}
        ).encode()
        with urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/api/do",
                data,
                {"Content-Type": "application/json"},
            ),
            timeout=10,
        ) as result:
            return json.load(result)

    yield deskd, request
    server.shutdown()
    server.server_close()
    thread.join()
    deskd._DESKS.clear()
    deskd._SCENES.clear()


def setup_texts(door):
    deskd, request = door
    with deskd.Session("editor-test", "maker") as desk:
        root = desk.world.root
    request("look")
    first = request(f'do create {root} kind=note title="first" text="Upper text."')["created"][0]
    second = request(f'do create {root} kind=note title="second" text="Lower text."')["created"][0]
    with deskd.Session("editor-test", "maker") as desk:
        w = desk.world
        reads = []
        for ident in (first, second):
            node = w.nodes[ident]
            subject = w.subjects[node["subject"]]
            reads.extend(
                [[ident, node["rev"], ["place"]], [subject["id"], subject["rev"], ["text"]]]
            )
        observed = {
            "item": second,
            "rev": w.nodes[second]["rev"],
            "reads": reads,
            "at": len(w.events),
        }
    return first, second, observed


def test_other_painted_text_is_seen_by_its_own_identity(door):
    first, second, observed = setup_texts(door)
    _, request = door
    response = request(
        f'do rewrite {first} text="Upper text.Lower text."', "fresh-viewer", observed
    )
    assert not response.get("error"), response
    assert response["events"]
    # The same viewer still has no permission-by-observation for arbitrary text.
    request("look")
    with door[0].Session("editor-test", "maker") as desk:
        root = desk.world.root
    hidden = request(f'do create {root} kind=note title="unseen" text="Private draft"')["created"][
        0
    ]
    refused = request(f'do rewrite {hidden} text="Overwrite"', "fresh-viewer")
    assert "not looked" in refused["error"]


def test_changed_neighbor_refuses_without_any_edit(door):
    first, _, observed = setup_texts(door)
    deskd, request = door
    request(f"read {first} :3")
    assert not request(f'do rewrite {first} text="Changed by its writer"').get("error")
    with deskd.Session("editor-test", "maker") as desk:
        before = len(desk.world.events)
    response = request(f'do rewrite {first} text="Stale join"', "fresh-viewer", observed)
    assert "changed" in response["error"]
    with deskd.Session("editor-test", "maker") as desk:
        assert len(desk.world.events) == before
        assert (
            desk.world.subjects[desk.world.nodes[first]["subject"]]["text"]
            == "Changed by its writer"
        )


def test_unrelated_neighbor_property_does_not_block_text_edit(door):
    first, _, observed = setup_texts(door)
    _, request = door
    request(f"read {first} :3")
    assert not request(f"do prop {first} color=blue").get("error")
    response = request(
        f'do rewrite {first} text="Upper text.Lower text."', "fresh-viewer", observed
    )
    assert not response.get("error"), response


def leaves(node):
    yield node
    for child in node.get("kids", []):
        yield from leaves(child)


def test_computed_text_records_member_state_and_text_revision(door):
    import lens_ir
    import scene

    first, second, _ = setup_texts(door)
    deskd, request = door
    source = f"""root : column, of {second}, each part
part : text "$text"
  on edit do rewrite $item text="$value"
  on key Backspace do rewrite {first} text="$(join($text of {first}))$value"
"""
    with deskd.Session("editor-test", "maker") as desk:
        tree = lens_ir.evaluate(desk, source)
        scene.emit(tree)
        part = next(n for n in leaves(tree) if n.get("part") == "part")
        observed = dict(part["fence"], at=len(desk.world.events))
        sid = desk.world.nodes[first]["subject"]
        assert any(r[0] == sid and "text" in r[2] for r in observed["reads"])
    result = request(f'do rewrite {first} text="Upper text.Lower text."', "fresh-viewer", observed)
    assert not result.get("error"), result
    again = request(f'do rewrite {first} text="Stale text"', "fresh-viewer", observed)
    assert "changed" in again["error"]


def test_conversation_target_survives_document_child_changes_but_not_retargeting(door):
    import lens_ir
    import scene

    deskd, request = door
    request("look")
    with deskd.Session("editor-test", "maker") as desk:
        root = desk.world.root
    doc = request(f'do create {root} kind=surface title="Document" layout=column')["created"][0]
    chat = request(f'do create {root} kind=chat title="Conversation"')["created"][0]
    request(f"do prop {doc} talk={chat}")
    source = f"""root : column, of {doc} as d, each sheet
sheet : column
  message : text ""
    on edit do append $d.talk line="$value"
"""
    with deskd.Session("editor-test", "maker") as desk:
        tree = lens_ir.evaluate(desk, source)
        scene.emit(tree)
        part = next(n for n in leaves(tree) if n.get("part") == "message")
        observed = dict(part["fence"], at=len(desk.world.events))
        assert next(r[2] for r in observed["reads"] if r[0] == doc) == ["prop:talk"]
    request(f"look {doc}")
    assert not request(f'do create {doc} kind=note title="new paragraph"').get("error")
    sent = request(
        f'do append {chat} line="This still belongs to this conversation"', "fresh-viewer", observed
    )
    assert not sent.get("error"), sent
    request(f"read {doc} :3")
    request(f"do prop {doc} talk={root}")
    refused = request(
        f'do append {chat} line="This must not go to an old conversation"', "fresh-viewer", observed
    )
    assert "changed" in refused["error"]
