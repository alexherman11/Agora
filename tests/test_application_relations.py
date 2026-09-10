"""Related objects preserve identity and cannot escape a view's subject binding."""

import copy

import pytest

from agora3.packages import source_digest
from agora3.world import Refusal
from tests.test_applications import bundle, call, request, surface, watermark
from tests.test_applications import setup as setup


def install_related(setup):
    gateway, actor = setup
    release = bundle("test.discussions")
    app = release["source"]["manifest"]["application"]
    app["schemas"]["test.thread"] = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "messages": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["subject", "messages"],
        "additionalProperties": False,
    }
    app["relations"] = {
        "threads": {
            "facet": "test.thread",
            "subject_field": "subject",
            "write": True,
            "max_items": 2,
        }
    }
    release["sha256"] = source_digest(release["source"])
    call(setup, "import", bundle=release)
    page = surface(setup, "test.discussions")
    return release, page


def related_change(oid, subject, revision=0):
    return {
        "id": oid,
        "expected_revision": revision,
        "facets": {"test.thread": {"subject": subject, "messages": ["Original discussion"]}},
    }


def test_related_access_and_revision_guard_are_enforced_atomically(setup):
    gateway, actor = setup
    _, page = install_related(setup)
    subject = page["context"]["subject"]
    original = request(setup, page, "read")
    request(
        setup,
        page,
        "related.transact",
        relation="threads",
        changes=[related_change("thread-one", subject)],
        subject_revision=original["revision"],
    )
    gateway.commit(actor, [related_change("foreign-thread", "another-subject")])
    gateway.commit(
        actor,
        [
            {
                "id": "thread-one",
                "expected_revision": 1,
                "facets": {"core.text": {"text": "Outside the relation grant"}},
            }
        ],
    )
    visible = request(setup, page, "related.query", relation="threads")["items"]
    assert [row["id"] for row in visible] == ["thread-one"]
    assert set(visible[0]["facets"]) == {"test.thread"}
    before = watermark(gateway)
    for change in [
        related_change("foreign-thread", subject, 1),
        related_change("thread-one", "another-subject", 2),
        {
            "id": "thread-one",
            "expected_revision": 2,
            "facets": {"core.text": {"text": "Not allowed"}},
        },
    ]:
        with pytest.raises(Refusal):
            request(setup, page, "related.transact", relation="threads", changes=[change])
    assert watermark(gateway) == before
    request(
        setup,
        page,
        "transact",
        changes=[
            {
                "id": subject,
                "expected_revision": original["revision"],
                "facets": {"core.text": {"text": "Changed"}},
            }
        ],
    )
    before = watermark(gateway)
    with pytest.raises(Refusal):
        request(
            setup,
            page,
            "related.transact",
            relation="threads",
            changes=[related_change("thread-two", subject)],
            subject_revision=original["revision"],
        )
    assert watermark(gateway) == before
    assert gateway.world.verify()["ok"]


def test_relation_limit_revocation_and_update_cannot_expand_scope(setup):
    gateway, _ = setup
    release, page = install_related(setup)
    subject = page["context"]["subject"]
    for oid in ("thread-one", "thread-two"):
        request(
            setup,
            page,
            "related.transact",
            relation="threads",
            changes=[related_change(oid, subject)],
        )
    with pytest.raises(Refusal, match="item limit"):
        request(
            setup,
            page,
            "related.transact",
            relation="threads",
            changes=[related_change("thread-three", subject)],
        )
    revised = copy.deepcopy(release)
    revised["source"]["manifest"]["application"]["relations"]["threads"]["max_items"] = 100
    revised["sha256"] = source_digest(revised["source"])
    call(setup, "import", bundle=revised, expected_revision=1)
    with pytest.raises(Refusal, match="related-object access"):
        call(setup, "refresh", view=page["view"]["id"])
    call(setup, "close", view=page["view"]["id"])
    with pytest.raises(Refusal, match="closed"):
        request(setup, page, "related.query", relation="threads")
    assert gateway.world.get("thread-one")["revision"] == 1
    assert gateway.world.verify()["ok"]
