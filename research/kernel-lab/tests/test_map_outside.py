"""What the map sends to an outside service (security review, 28 Oct 2026): a found thing's title, an ambiguous name and
an id the caller can't see all went to Nominatim. Only typed text that names nothing in the world goes out. The real
geocode runs with only its HTTP layer stubbed (the URLs are recorded); the ground is faked. Fresh temporary world."""
import importlib.util
import shutil
import sys
import tempfile
import urllib.parse
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from kernel.kernel import Kernel, Actor  # noqa: E402

spec = importlib.util.spec_from_file_location("map_outside_under_test", LAB / "modules" / "map" / "map.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
URLS = []


class FakeHttp:
    def get(self, url, rng=None, timeout=8):
        URLS.append(url)
        return 200, "[]"


class FakeGround:
    def find(self, text, limit=8):
        return []

    def route(self, stops, mode="walk"):
        return dict(path=list(stops), metres=420, minutes=6, legs=[], streets=["Elm St"])

    def contains(self, *a):
        return False


class FakeCall(M.Call):
    def __init__(self, k, person):
        super().__init__({"use": "u1", "caller": {"person": person}})
        self.k, self.who = k, person

    def see(self, line):
        out = self.k.run(Actor(self.who, self.who, "person"), line, mode="see")
        if not out.get("ok"):
            raise ValueError(out.get("text"))
        self.k.outside_marks(self.who, out.get("rows"))          # as kernel.module_see marks a module's reads
        return out.get("rows", []), out.get("text", "")


def sent():
    out = [urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("q", [""])[0] for u in URLS]
    URLS.clear()
    M.geo_cache.clear()
    return out


@pytest.fixture
def world(monkeypatch):
    monkeypatch.setattr(M, "tiles", lambda: type("T", (), {"http": FakeHttp()})())
    monkeypatch.setattr(M.time, "sleep", lambda s: None)
    monkeypatch.setattr(M, "home_ground", lambda call, m, near=None: FakeGround())
    monkeypatch.setattr(M, "area", lambda lat, lon, radius=1500: FakeGround())
    M.geo_last[0] = 0
    d = tempfile.mkdtemp(prefix="map-outside-")
    k = Kernel(d, {"tag": "dk", "name": "Seabright", "steward": {"account": "a", "name": "Alex"}})
    alex = k.accounts["a"]
    run = lambda line: k.run(Actor(alex, alex, "person"), line)
    run("make kind=map name=Town centre=36.97123,-122.01456")
    run('make kind=meeting title="Review lease with the landlord" sees=me')
    run('make kind=note title=Dentist sees=me')
    run('make kind=note title=Dentist sees=me')
    sent()
    yield k, alex
    URLS.clear()
    shutil.rmtree(d, ignore_errors=True)


def show(k, who, text):
    try:
        M.w_show(FakeCall(k, who), {"target": None, "words": text, "kv": {}})
        return ""
    except ValueError as exc:
        return str(exc)


def test_a_found_things_title_never_goes_outside(world):
    k, alex = world
    why = show(k, alex, "Review lease with the landlord")
    assert sent() == []
    assert "has no place the map can read" in why


def test_an_ambiguous_name_asks_which_and_sends_nothing(world):
    k, alex = world
    why = show(k, alex, "Dentist")
    assert sent() == []
    assert "things are called Dentist" in why


def test_an_id_is_never_a_search(world):
    k, alex = world
    show(k, alex, "dk9")
    assert sent() == []


def test_typed_text_that_names_nothing_may_go_out(world):
    k, alex = world
    show(k, alex, "Pleasure Point")
    assert sent() == ["Pleasure Point"]


def near(k, who):
    try:
        M.w_near(FakeCall(k, who), {"target": None, "words": "36.97,-122.01", "kv": {"within": "5000"}})
    except ValueError:
        pass
    return sent()


def test_drawing_sends_public_place_text_and_the_askers_own_only(world):
    """Alex, 28 Oct: "Public, or my own". A group's private place text never leaves while the map draws."""
    k, alex = world
    pike = k.join("p", "Pike", invite={"admitted": "member"})["person"]
    run = lambda who, line: k.run(Actor(who, who, "person"), line)
    run(alex, 'make kind=note title=Beach location="Seabright State Beach"')            # public
    run(alex, 'make kind=note title=Therapy location="Dr Ames psychiatry, 14 Oak St" sees=me')   # Alex's own
    crew = run(alex, "group name=crew open=no")["text"].split()[2]
    run(alex, f"role {pike} member in={crew}")
    out = run(pike, f'make kind=note title=Shelter location="Harbor shelter intake, 5 Elm" in={crew}')
    assert out["ok"], out["text"]
    got = near(k, alex)
    assert "Seabright State Beach" in got
    assert "Dr Ames psychiatry, 14 Oak St" in got                    # his own, as he chose
    assert "Harbor shelter intake, 5 Elm" not in got                 # the group's, not public, not his


def test_a_row_without_the_kernels_answer_is_private(world):
    k, alex = world
    row = {"id": "dk1", "location": "Seabright State Beach"}
    assert M.position(FakeCall(k, alex), lambda: FakeGround(), row) is None
    assert sent() == []


def crew_world(k, alex):
    pike = k.join("p", "Pike", invite={"admitted": "member"})["person"]
    run = lambda who, line: k.run(Actor(who, who, "person"), line)
    crew = run(alex, "group name=crew open=no")["text"].split()[2]
    run(alex, f"role {pike} member in={crew}")
    town = next(t for t in k.things("map"))
    return pike, run, crew, town


def test_replanning_someone_elses_route_never_sends_its_saved_stops(world):
    """Approved-builds review H3: replanning a crew route sent its stored stops out as if the caller typed them."""
    k, alex = world
    pike, run, crew, town = crew_world(k, alex)
    route = run(pike, f'make kind=route map={town} name=Run stops="Harbor shelter intake, 5 Elm > 36.975,-122.02" '
                      f'in={crew}')["made"][0]
    with pytest.raises(ValueError):
        M.w_route(FakeCall(k, alex), {"target": route, "words": "", "kv": {}})
    assert sent() == []


def test_a_layers_saved_search_is_not_run_for_someone_else(world):
    k, alex = world
    pike, run, crew, town = crew_world(k, alex)
    out = run(pike, f'make kind=map-layer map={town} name=Shelters shows="map.find Harbor shelter" in={crew}')
    assert out["ok"], out["text"]
    rows = M.w_layers(FakeCall(k, alex), {"target": town, "words": "", "kv": {}})["rows"]
    layer = next(r for r in rows if r.get("name") == "Shelters")
    assert "goes outside only for them" in layer.get("error", "")
    assert sent() == []
