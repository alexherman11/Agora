"""Map/board place integration, no windows and no outside requests."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
BOARD = LAB.parent / "community-app" / "board"
sys.path[:0] = [str(LAB), str(BOARD)]
from kernel.kernel import Kernel


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = load("panel_map", LAB / "modules/map/map.py")
B = load("panel_board", BOARD / "board.py")
I = load("panel_install", LAB / "apps/map/install.py")


class Call(M.Call):
    def __init__(self, k, actor):
        super().__init__({"use": "test", "caller": {"person": actor.person}})
        self.k, self.actor = k, actor

    def see(self, line):
        out = self.k.run(self.actor, line, mode="see")
        assert out["ok"], out
        return out.get("rows", []), out.get("text", "")


def test_board_kinds_accept_optional_place(monkeypatch):
    definitions = json.loads((BOARD / "definitions.json").read_text())["kinds"]
    for i, kind in enumerate(definitions):
        kind.update(id=f"mp{i+10}", rev=1)
    monkeypatch.setattr(B, "read", lambda *a: [{"at": "2026-10-29T00:00:00Z"}])
    monkeypatch.setattr(B, "rows", lambda use, kind: definitions if kind == "kind" else [
        dict(id="mp1", rev=1, group="mp2")])
    monkeypatch.setattr(B, "leader", lambda *a: True)
    monkeypatch.setitem(B.hello, "place", "mp2")
    for kind in definitions:
        fields = dict(text="Meet by the garden", place="36.9672,-122.0088",
                      post_kind=kind["name"], **{"in": "mp2"})
        fields.update({key: {"seats": "3", "start": "2026-11-01T10:00:00Z",
                            "closes": "2026-11-01T09:00:00Z", "options": "yes no"}[key]
                       for key in kind.get("required", "").split()})
        result = B.call(dict(use="test", word="board.post", caller=dict(person="mp3"), args=dict(kv=fields)))
        assert 'place="36.9672,-122.0088"' in result["lines"][0]
        assert f'post_kind="{kind["name"]}"' in result["lines"][0]


def test_visible_place_links_become_board_pins_and_hidden_places_do_not(tmp_path):
    k = Kernel(tmp_path / "world", dict(tag="mp", name="Panel test",
        steward=dict(account="alex", name="Alex"), invites_counted_by="kernel",
        invites=[dict(code="x", uses=2)]))
    alex = k.actor_for(k.accounts["alex"])
    bea = k.actor_for(k.join("bea", "Bea", invite="x")["person"])

    def make(line, actor=alex):
        out = k.run(actor, line)
        assert out["ok"], out
        return out["made"][0]

    place = make('make kind=spot name="Garden" lat=36.9672 lon=-122.0088')
    secret = make('make kind=spot name="Private garden" sees=me lat=36.968 lon=-122.009')
    posts = [make(f'post text="Garden {kind}" post_kind={kind} place={place}')
             for kind in ("event", "ask", "offer", "discussion")]
    private_link = make(f'post text="Private place" place={secret}')
    # Alex has used the ordinary five-post allowance. A second member supplies
    # the no-place control without changing the production quota or visibility.
    no_place = make('post text="No place"', actor=bea)
    call = Call(k, bea)
    rows, _ = call.see("rows post")
    def no_ground():
        pytest.fail("linked world places must not fetch ground or geocode")
    pins = M.placed(call, no_ground, rows)
    assert {r["id"] for r in pins} == set(posts)
    assert {r["post_kind"] for r in pins} == {"event", "ask", "offer", "discussion"}
    assert all((r["lat"], r["lon"]) == (36.9672, -122.0088) for r in pins)
    assert private_link not in {r["id"] for r in pins}
    assert no_place not in {r["id"] for r in pins}
    assert place in call.saw
    k.run(alex, "look " + place)
    assert k.run(alex, f"set {place} lat=36.969")["ok"]
    assert all(p["lat"] == 36.969 for p in M.placed(Call(k, bea), no_ground, rows))


def test_installer_preserves_existing_layers_and_adds_board_reading():
    assert ("Board", "board.feed", "pin", "#527f68", 5) in I.LAYERS
    assert {"map-panel", "geo-map", "map-layers"} <= I.COMPONENTS.keys()
    source = I.code()
    result = subprocess.run(["node", "--input-type=module", "--check"], input=source,
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_panel_state_and_pin_actions_without_browser():
    result = subprocess.run(["node", str(LAB / "apps/map/test-panel.cjs")],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "panel checks passed" in result.stdout
