"""dk2834: a button dispatcher is an act, even when its current line only reads.

Fresh hidden worlds and authenticated loopback HTTP only; no desktop or live buttons.
"""
import importlib.util
import json
import sys
import threading
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(LAB), str(LAB / "tests")]
from kernel import scratch
from kernel.door import serve
from kernel.kernel import Kernel, Tx
from kernel.words import PRESS_MODE_HELP
from test_skeleton import StandInEntry, post

spec = importlib.util.spec_from_file_location("press_mcp", LAB / "mcp" / "agora_mcp.py")
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)


@pytest.fixture
def world():
    with scratch.TemporaryDirectory(prefix="press-modes-") as folder:
        k = Kernel(folder, {"tag": "pm", "name": "Press fixture",
                            "steward": {"account": "tester", "name": "Tester"}})
        entry = StandInEntry("fixture-secret")
        entry.sessions["fixture-session"] = {"account": "tester", "method": "google"}
        srv, host = serve(k, entry.url, "fixture-secret", 0, LAB)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"

        def call(line, mode="do", ok=True):
            code, out = post(url + "/" + mode, {"line": line}, token="fixture-session")
            assert code == 200, out
            assert out["ok"] == ok, out
            return out

        try:
            yield k, call, url
        finally:
            srv.shutdown()
            srv.server_close()
            host.stop_all()
            entry.srv.shutdown()
            entry.srv.server_close()


def test_press_dictionary_and_help_are_do(world):
    k, call, _ = world
    rows = call("help", "see")["rows"]
    assert next(r for r in rows if r["word"] == "press")["kind"] == "do"
    help_out = call("help press", "see")
    assert "a do word" in help_out["text"]
    assert PRESS_MODE_HELP in help_out["text"]
    assert k.entry(k.find_entry("press"))["word_kind"] == "do"


@pytest.mark.parametrize("button_line", ["make kind=note text=changed", "look",
                                        "press Inner"])
@pytest.mark.parametrize("spelling", ["press Button", "do press Button"])
def test_see_refuses_before_dispatch(world, button_line, spelling):
    k, call, _ = world
    call('make kind=button label=Inner does="make kind=note text=nested"')
    call("make kind=button label=Button does=" + json.dumps(button_line))
    before, count = k.state.snapshot(), len(k.log.records)
    out = call(spelling, "see", ok=False)
    assert "/see runs only readings" in out["text"]
    assert "send it through /do" in out["text"]
    assert out["records"] == out["made"] == []
    assert k.state.snapshot() == before
    assert len(k.log.records) == count


def test_see_refuses_without_resolving_button_and_inside_reading_verb(world):
    k, call, _ = world
    call('make kind=button label=Button does="make kind=note text=changed"')
    call('verb peek kind_of=see steps="press Button" help="peek: fixture"')
    before, count = k.state.snapshot(), len(k.log.records)
    for line in ("press", "press Missing", "peek"):
        assert "send it through /do" in call(line, "see", ok=False)["text"]
    assert k.state.snapshot() == before
    assert len(k.log.records) == count


def test_do_press_has_the_same_act_receipt_and_undo_as_click_line(world):
    k, call, _ = world
    note = call("make kind=note text=before")["made"][0]
    line = f"set {note} text=after"
    call("make kind=button label=Button does=" + json.dumps(line))
    click = call(line)  # The button UI sends its does= line to /do.
    click_rec = k.log.records[-1]
    call("undo " + click["records"][0])
    assert k.state.get(note, "text") == "before"
    count = len(k.log.records)
    pressed = call("press Button")
    assert len(k.log.records) == count + 1
    assert pressed["records"] == [f"r{k.log.records[-1]['seq']}"]
    for field in ("by", "entry", "parts"):
        assert k.log.records[-1][field] == click_rec[field]
    assert k.state.get(note, "text") == "after"
    call("undo " + pressed["records"][0])
    assert k.state.get(note, "text") == "before"


def test_lines_router_sends_press_to_do(world):
    k, call, url = world
    call('make kind=button label=Button does="make kind=note text=routed"')
    door = mcp.Door(url, bearer="fixture-session")
    result = json.loads(door.batch("lines", ["help press", "press Button"])["content"][0]["text"])
    assert result["ok"]
    assert [r["via"] for r in result["receipts"]] == ["/see", "/do"]
    made = result["receipts"][1]["made"]
    assert len(made) == 1 and k.state.get(made[0], "text") == "routed"


def test_old_dictionary_upgrades_renamed_press_and_group_copy_once(world):
    k, call, _ = world
    press = k.find_entry("press")
    call("help press", "see")
    call(f"word-rename {press} to=push")
    call("help push", "see")
    call('word-set push aliases="press tap" help="My button help"')
    call("help push", "see")
    group = call("group name=Fixture")["made"][0]
    copied = call(f"dictionary-copy {press} word=localpush in={group}")["made"][0]
    # Recreate persisted metadata from before dk2834, without any live world.
    tx = Tx(k)
    tx.part("fixture", None, "old press classifications")
    for eid in (press, copied):
        tx.set(eid, "word_kind", "see")
    k._commit(tx, by="kernel", words="old fixture dictionary")
    restored = Kernel(k.dir)
    actor = restored.actor_for(restored.accounts["tester"])
    for eid in (press, copied):
        assert restored.state.get(eid, "word_kind") == "do"
        assert restored.state.get(eid, "help") == "My button help " + PRESS_MODE_HELP
    for line in ("push Missing", "press Missing", "tap Missing",
                 f"localpush Missing in={group}"):
        out = restored.run(actor, line, mode="see")
        assert not out["ok"] and "send it through /do" in out["text"]
    count = len(restored.log.records)
    assert Kernel(k.dir).state.snapshot() == restored.state.snapshot()
    assert len(Kernel(k.dir).log.records) == count
