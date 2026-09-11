import json

from agora3.gateway import Gateway
from agora3.package_catalog import catalog


def test_catalog_distinguishes_saved_and_installed_source_without_body_dump(tmp_path):
    g = Gateway(tmp_path)
    a = g.principal("human")
    manifest = {"runtime": "browser-1", "name": "Long source", "ui": {"entry": "index.html"}}
    files = {"index.html": "<!doctype html><body>" + ("long authored source " * 10000) + "</body>"}
    g.packages.save(a, id="test.reader", expected_revision=0, files=files, manifest=manifest)
    build = g.packages.build(a, id="test.reader", expected_revision=1)["build"]
    g.packages.install(a, id="test.reader", build=build, expected_revision=0)
    g.packages.save(
        a,
        id="test.reader",
        expected_revision=1,
        files=files | {"unused.txt": "saved later"},
        manifest=manifest,
    )
    result = catalog(g)
    item = result["packages"][0]
    assert item["package_id"] == "test.reader"
    assert item["source_object_id"] == "agora.package.test.reader"
    assert (
        item["source_revision"] == 2
        and item["installed_source_revision"] == 1
        and item["installation_revision"] == 1
    )
    assert len(json.dumps(result)) < 2500
    assert "long authored source" not in json.dumps(result)
    assert "uniqueItems" not in result["schema_keywords"]
    assert "maxItems" in result["schema_keywords"]


def test_uninstalled_package_has_no_implied_activation(tmp_path):
    g = Gateway(tmp_path)
    a = g.principal("human")
    g.packages.save(
        a,
        id="test.uninstalled",
        expected_revision=0,
        files={"index.html": "<p>draft</p>"},
        manifest={"runtime": "browser-1", "ui": {"entry": "index.html"}},
    )
    item = catalog(g)["packages"][0]
    assert item["installation_revision"] == 0 and item["installed_source_revision"] is None
