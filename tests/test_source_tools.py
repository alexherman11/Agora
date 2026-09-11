import pytest

from agora3.gateway import Gateway
from agora3.world import Refusal


@pytest.fixture
def setup(tmp_path):
    gateway = Gateway(tmp_path)
    actor = gateway.principal("human")
    gateway.dispatch(
        actor,
        "package.save",
        {
            "id": "demo",
            "expected_revision": 0,
            "files": {"index.html": "<p>Hello</p>\n<p>World</p>\n", "notes.txt": "same same"},
            "manifest": {"runtime": "browser-1", "ui": {"entry": "index.html"}},
        },
    )
    return gateway, actor


def test_read_search_and_exact_edit(setup):
    g, a = setup
    assert (
        g.dispatch(
            a,
            "package.read",
            {"id": "demo", "path": "index.html", "start_line": 2, "line_count": 1},
        )["content"]
        == "<p>World</p>\n"
    )
    assert (
        g.dispatch(a, "package.search", {"id": "demo", "text": "World"})["matches"][0]["line"] == 2
    )
    result = g.dispatch(
        a,
        "package.patch",
        {
            "id": "demo",
            "expected_revision": 1,
            "edits": [{"path": "index.html", "old": "World", "new": "Agora"}],
        },
    )
    assert result["revision"] == 2
    assert "facets" not in result["transaction"]["items"][0]
    assert "Hello" in g.packages.get("demo")["facets"]["agora.package"]["files"]["index.html"]
    assert g.packages.installation("demo")["revision"] == 0
    assert g.world.verify()["ok"]


@pytest.mark.parametrize(
    "edits",
    [
        [
            {"path": "index.html", "old": "Hello", "new": "changed"},
            {"path": "notes.txt", "old": "same", "new": "ambiguous"},
        ],
        [{"path": "index.html", "old": "absent", "new": "bad"}],
        [{"path": "index.html", "delete": True}],
        [{"path": "../escape", "content": "bad"}],
    ],
)
def test_invalid_batch_is_atomic(setup, edits):
    g, a = setup
    before = g.packages.get("demo")
    with pytest.raises(Refusal):
        g.dispatch(a, "package.patch", {"id": "demo", "expected_revision": 1, "edits": edits})
    assert g.packages.get("demo") == before


def test_stale_source_and_revoked_actor(setup):
    g, a = setup
    with pytest.raises(Refusal):
        g.dispatch(
            a,
            "package.patch",
            {"id": "demo", "expected_revision": 2, "edits": [{"path": "extra", "content": "x"}]},
        )
    g.revoke()
    with pytest.raises(Refusal):
        g.dispatch(a, "package.read", {"id": "demo"})


def test_read_truncation_is_explicit(setup):
    g, a = setup
    g.dispatch(
        a,
        "package.patch",
        {
            "id": "demo",
            "expected_revision": 1,
            "edits": [{"path": "long.txt", "content": "x" * 20000}],
        },
    )
    result = g.dispatch(a, "package.read", {"id": "demo", "path": "long.txt"})
    assert len(result["content"]) == 16000 and result["truncated"]
