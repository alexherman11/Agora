"""Shared subjects, bounded access, independent application lifecycle and portable code."""

import copy

import pytest

from agora3.gateway import Gateway
from agora3.packages import source_digest
from agora3.world import Refusal

ANNOTATIONS = {
    "type": "object",
    "properties": {"threads": {"type": "array", "maxItems": 64, "items": {"type": "object"}}},
    "required": ["threads"],
    "additionalProperties": False,
}


def bundle(package="test.notes", *, extra_read=None):
    facets = ["core.title", "core.text", "text.annotations"]
    source = {
        "id": package,
        "files": {"index.html": "<!doctype html><title>Application</title><p>Native text</p>"},
        "manifest": {
            "name": package,
            "runtime": "browser-1",
            "ui": {"entry": "index.html", "mount": "application"},
            "application": {
                "protocol": "agora.application/1",
                "accepts": ["core.text"],
                "read_facets": facets + ([extra_read] if extra_read else []),
                "write_facets": facets,
                "size": {"width": 320, "height": 280},
                "create": {"core.title": {"text": "Untitled"}, "core.text": {"text": ""}},
                "schemas": {"text.annotations": ANNOTATIONS},
            },
        },
    }
    return {
        "format": "agora.application-bundle/1",
        "source": source,
        "sha256": source_digest(source),
    }


@pytest.fixture
def setup(tmp_path):
    gateway = Gateway(tmp_path)
    actor = gateway.principal("human")
    for package in ("test.notes", "test.documents"):
        gateway.dispatch(actor, "application.import", {"bundle": bundle(package)})
    return gateway, actor


def call(setup, name, **args):
    gateway, actor = setup
    return gateway.dispatch(actor, "application." + name, args)


def surface(setup, package="test.notes", subject=None):
    view = call(setup, "open", package=package, **({"subject": subject} if subject else {}))
    return call(setup, "surface", view=view["id"])


def request(setup, page, method, **args):
    context = page["context"]
    return call(
        setup, "request", view=context["view"], lease=context["lease"], method=method, args=args
    )


def change(obj, **facets):
    return {"id": obj["id"], "expected_revision": obj["revision"], "facets": facets}


def watermark(gateway):
    return gateway.world.query(limit=1)["watermark"]


def test_two_applications_share_one_subject_with_independent_state(setup):
    gateway, _ = setup
    note = surface(setup)
    document = surface(setup, "test.documents", note["context"]["subject"])
    obj = request(setup, note, "read")
    result = request(
        setup, note, "transact", changes=[change(obj, **{"core.text": {"text": "One shared text"}})]
    )
    assert request(setup, document, "read")["facets"]["core.text"]["text"] == "One shared text"
    assert result["items"][0]["written_by"] == "human:test.notes"
    request(setup, note, "state.set", state={"draft": "Note draft", "selection": [1, 3]})
    request(setup, document, "state.set", state={"draft": "Editor draft"})
    assert request(setup, note, "state.get")["state"]["draft"] == "Note draft"
    assert request(setup, document, "state.get")["state"]["draft"] == "Editor draft"
    before = gateway.world.get(obj["id"])
    call(
        setup,
        "position",
        view=note["view"]["id"],
        bounds={"x": 80, "y": 50, "width": 300, "height": 240},
    )
    assert gateway.world.get(obj["id"]) == before
    assert gateway.world.verify()["ok"]


def test_scope_rejects_other_subjects_facets_and_management_without_writes(setup):
    gateway, actor = setup
    note, other = surface(setup), surface(setup)
    target = request(setup, note, "read")
    foreign = request(setup, other, "read")
    gateway.commit(actor, [change(target, **{"core.draft": {"secret": "private unrelated facet"}})])
    assert "core.draft" not in request(setup, note, "read")["facets"]
    invalid = [
        ("read", {"id": foreign["id"]}),
        ("transact", {"changes": [change(foreign, **{"core.text": {"text": "attack"}})]}),
        ("transact", {"changes": [change(target, **{"core.draft": {}})]}),
        (
            "transact",
            {
                "changes": [
                    change(target, **{"core.text": {"text": "partial"}}),
                    change(foreign, **{"core.text": {"text": "attack"}}),
                ]
            },
        ),
        ("guest.execute", {"command": "true"}),
        ("application.open", {"package": "test.documents"}),
        ("world.query", {}),
        ("state.get", {"view": other["view"]["id"]}),
    ]
    before = watermark(gateway)
    for name, args in invalid:
        with pytest.raises(Refusal):
            request(setup, note, name, **args)
        assert watermark(gateway) == before
    assert "private unrelated facet" not in str(request(setup, note, "read"))
    assert gateway.world.verify()["ok"]


def test_stale_edit_keeps_other_writer_and_retained_draft(setup):
    gateway, _ = setup
    note = surface(setup)
    editor = surface(setup, "test.documents", note["context"]["subject"])
    original = request(setup, note, "read")
    request(
        setup,
        note,
        "transact",
        changes=[change(original, **{"core.text": {"text": "first writer"}})],
    )
    request(
        setup,
        editor,
        "state.set",
        state={"draft": "second writer", "base_revision": original["revision"]},
    )
    before = watermark(gateway)
    with pytest.raises(Refusal, match="Stale write"):
        request(
            setup,
            editor,
            "transact",
            changes=[change(original, **{"core.text": {"text": "second writer"}})],
        )
    assert watermark(gateway) == before
    assert request(setup, note, "read")["facets"]["core.text"]["text"] == "first writer"
    assert request(setup, editor, "state.get")["state"]["draft"] == "second writer"


def test_refresh_preserves_other_browsers_lease_and_drafts(setup):
    gateway, _ = setup
    note, other = surface(setup), surface(setup, "test.documents")
    request(setup, note, "state.set", state={"selection": [4, 7], "draft": "keep this"})
    update = bundle()
    update["source"]["files"]["index.html"] += "<p>Version two</p>"
    update["sha256"] = source_digest(update["source"])
    call(setup, "import", bundle=update, expected_revision=1)
    assert "Version two" not in call(setup, "surface", view=note["view"]["id"])["html"]
    call(setup, "refresh", view=note["view"]["id"])
    refreshed = call(setup, "surface", view=note["view"]["id"])
    assert "Version two" in refreshed["html"]
    assert request(setup, refreshed, "state.get")["state"]["draft"] == "keep this"
    # A second browser using the same view can still flush its own draft.
    assert request(setup, note, "read")
    request(setup, note, "state.set", state={"draft": "second browser retained"})
    assert request(setup, refreshed, "state.get")["state"]["draft"] == "second browser retained"
    before = watermark(gateway)
    call(setup, "refresh", view=note["view"]["id"])
    assert watermark(gateway) == before  # Same publication is idempotent.
    call(setup, "close", view=note["view"]["id"])
    with pytest.raises(Refusal, match="closed, refreshed or revoked"):
        request(setup, note, "read")
    assert request(setup, other, "read")
    assert (
        call(setup, "surface", view=other["view"]["id"])["context"]["lease"]
        == other["context"]["lease"]
    )
    assert gateway.world.verify()["ok"]


def test_update_cannot_widen_existing_grant(setup):
    gateway, _ = setup
    note = surface(setup)
    call(setup, "import", bundle=bundle(extra_read="core.draft"), expected_revision=1)
    before = watermark(gateway)
    with pytest.raises(Refusal, match="broader access"):
        call(setup, "refresh", view=note["view"]["id"])
    assert watermark(gateway) == before
    assert (
        "core.draft"
        not in call(setup, "surface", view=note["view"]["id"])["context"]["grant"]["read_facets"]
    )


def test_uninstall_preserves_content_schema_and_other_app_then_reinstall_reopens_draft(setup):
    gateway, _ = setup
    note = surface(setup)
    editor = surface(setup, "test.documents", note["context"]["subject"])
    obj = request(setup, note, "read")
    request(
        setup,
        note,
        "transact",
        changes=[change(obj, **{"text.annotations": {"threads": [{"text": "shared comment"}]}})],
    )
    request(setup, note, "state.set", state={"draft": "retained"})
    expected = request(setup, editor, "read")
    exported = call(setup, "export", package="test.notes")
    call(setup, "uninstall", package="test.notes", expected_revision=1)
    with pytest.raises(Refusal):
        request(setup, note, "read")
    assert request(setup, editor, "read") == expected
    assert gateway.world.get("agora.schema.text.annotations")
    assert {app["package"] for app in call(setup, "list")["applications"]} == {"test.documents"}
    call(setup, "import", bundle=exported, expected_revision=1)
    call(setup, "reopen", view=note["view"]["id"])
    restored = call(setup, "surface", view=note["view"]["id"])
    assert request(setup, restored, "state.get")["state"]["draft"] == "retained"
    assert gateway.world.verify()["ok"]


def test_bundle_installs_into_fresh_world_without_copying_content_or_state(setup, tmp_path):
    page = surface(setup)
    request(setup, page, "state.set", state={"private": "do not distribute"})
    exported = call(setup, "export", package="test.notes")
    assert "do not distribute" not in str(exported)
    assert page["context"]["subject"] not in str(exported)
    fresh = Gateway(tmp_path / "recipient")
    recipient = fresh.principal("human")
    call((fresh, recipient), "import", bundle=exported)
    assert call((fresh, recipient), "list")["applications"][0]["package"] == "test.notes"
    assert call((fresh, recipient), "list")["views"] == []
    assert fresh.world.query(["core.text"])["items"] == []
    assert fresh.world.verify()["ok"]


def test_corrupt_bundle_or_stale_source_does_not_activate(setup):
    gateway, _ = setup
    bad = bundle("test.corrupt")
    bad["source"]["files"]["index.html"] = "tampered"
    before = watermark(gateway)
    with pytest.raises(Refusal, match="checksum"):
        call(setup, "import", bundle=bad)
    assert watermark(gateway) == before
    with pytest.raises(Refusal, match="Stale write"):
        call(setup, "import", bundle=bundle(), expected_revision=0)
    assert watermark(gateway) == before


def test_new_subject_validation_is_atomic_with_view_creation(setup):
    gateway, _ = setup
    invalid = bundle("test.invalid")
    invalid["source"]["manifest"]["application"]["create"]["core.text"] = {"text": 123}
    invalid["sha256"] = source_digest(invalid["source"])
    call(setup, "import", bundle=invalid)
    before = watermark(gateway)
    with pytest.raises(Refusal, match="Schema mismatch"):
        call(setup, "open", package="test.invalid")
    assert watermark(gateway) == before
    assert not call(setup, "list")["views"]


def test_schema_conflict_does_not_replace_an_installed_application(setup):
    gateway, _ = setup
    original = gateway.packages.installation("test.notes")
    modified = copy.deepcopy(bundle())
    schema = modified["source"]["manifest"]["application"]["schemas"]["text.annotations"]
    schema["properties"]["threads"]["maxItems"] = 63
    modified["sha256"] = source_digest(modified["source"])
    with pytest.raises(Refusal):
        call(setup, "import", bundle=modified, expected_revision=1)
    assert gateway.packages.installation("test.notes") == original


def test_delegation_revocation_blocks_existing_application_lease(setup):
    gateway, _ = setup
    note = surface(setup)
    gateway.revoke()
    with pytest.raises(Refusal, match="stopped or replaced"):
        request(setup, note, "read")


def test_reopening_cannot_bypass_the_active_view_limit(setup):
    gateway, _ = setup
    first = surface(setup)
    call(setup, "close", view=first["view"]["id"])
    for _ in range(32):
        call(setup, "open", package="test.notes", subject=first["context"]["subject"])
    before = watermark(gateway)
    with pytest.raises(Refusal, match="32 open views"):
        call(setup, "reopen", view=first["view"]["id"])
    assert watermark(gateway) == before


def test_malformed_facet_declaration_is_an_instructive_atomic_refusal(setup):
    gateway, _ = setup
    malformed = bundle("test.malformed")
    malformed["source"]["manifest"]["application"]["accepts"] = [["core.text"]]
    malformed["sha256"] = source_digest(malformed["source"])
    before = watermark(gateway)
    with pytest.raises(Refusal, match="facet names"):
        call(setup, "import", bundle=malformed)
    assert watermark(gateway) == before
