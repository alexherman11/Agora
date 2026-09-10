import copy

import pytest

from agora3.browser_assembly import assemble
from agora3.gateway import Gateway
from agora3.world import Refusal


def source():
    return {
        "id": "agora.shell",
        "files": {
            "index.html": '<head><!-- agora:styles --></head><body><div id="root"></div>'
            "<!-- agora:scripts --></body>",
            "a.js": 'window.order=["a"]',
            "b.js": 'window.order.push("b")',
            "ui.css": "#root{color:red}",
        },
        "manifest": {
            "runtime": "browser-1",
            "ui": {"entry": "index.html", "scripts": ["a.js", "b.js"], "styles": ["ui.css"]},
        },
    }


def test_order_reproducibility_and_source_preservation():
    s = source()
    before = copy.deepcopy(s)
    a = assemble(s)
    assert a == assemble(s) and s == before
    assert a["html"].index(s["files"]["a.js"]) < a["html"].index(s["files"]["b.js"])
    assert 'data-agora-source="ui.css"' in a["html"]


@pytest.mark.parametrize(
    "mutation",
    ["missing", "duplicate", "marker_missing", "marker_duplicate", "close_tag", "external"],
)
def test_invalid_assembly_is_refused(mutation):
    s = source()
    if mutation == "missing":
        s["manifest"]["ui"]["scripts"] = ["missing.js"]
    if mutation == "duplicate":
        s["manifest"]["ui"]["scripts"] = ["a.js", "a.js"]
    if mutation == "marker_missing":
        s["files"]["index.html"] = "<body></body>"
    if mutation == "marker_duplicate":
        s["files"]["index.html"] += "<!-- agora:scripts -->"
    if mutation == "close_tag":
        s["files"]["a.js"] = 'let x="</ScRiPt>"'
    if mutation == "external":
        s["manifest"]["ui"]["scripts"] = ["https://example.org/a.js"]
    with pytest.raises(Refusal):
        assemble(s)


def test_build_install_and_restore_use_exact_retained_artifact(tmp_path):
    g = Gateway(tmp_path)
    actor = g.principal("human")
    s = source()
    g.packages.save(
        actor, id=s["id"], expected_revision=0, files=s["files"], manifest=s["manifest"]
    )
    first = g.packages.build(actor, id=s["id"], expected_revision=1)
    g.packages.install(actor, id=s["id"], build=first["build"], expected_revision=0)
    html1, rev1 = g.packages.shell()
    assert "window.order" in html1 and rev1 == 1
    s["files"]["b.js"] = 'window.order.push("changed")'
    g.packages.save(
        actor, id=s["id"], expected_revision=1, files=s["files"], manifest=s["manifest"]
    )
    assert g.packages.shell()[0] == html1
    second = g.packages.build(actor, id=s["id"], expected_revision=2)
    g.packages.install(actor, id=s["id"], build=second["build"], expected_revision=1)
    assert "changed" in g.packages.shell()[0]
    g.packages.install(actor, id=s["id"], build=first["build"], expected_revision=2, restore=True)
    assert g.packages.shell()[0] == html1


def test_legacy_self_contained_html_remains_valid(tmp_path):
    g = Gateway(tmp_path)
    actor = g.principal("human")
    g.packages.save(
        actor,
        id="agora.shell",
        expected_revision=0,
        files={"index.html": "<p>old</p>"},
        manifest={"runtime": "browser-1", "ui": {"entry": "index.html"}},
    )
    build = g.packages.build(actor, id="agora.shell", expected_revision=1)
    g.packages.install(actor, id="agora.shell", build=build["build"], expected_revision=0)
    assert g.packages.shell()[0] == "<p>old</p>"
