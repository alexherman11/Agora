"""Memory-only boundary checks: no disk fixture, process, desktop or live world.

These exercise actual selection/dispatch/read filtering. They do not replace
House's persisted-world admission and feature tests.
"""
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel import document_scope as docs, lines as L
from kernel.kernel import Actor, Kernel, Refused


def memory_kernel():
    k = Kernel.__new__(Kernel)
    facts = {
        "ds1": dict(kind="document-library", groups=["ds10"]),
        "ds2": dict(kind="document-library", groups=["ds10"]),
        "ds3": dict(kind="document-folder", library="ds1", parent="ds1",
                    visibility_of="ds1", groups=["ds10"]),
        "ds4": dict(kind="document-folder", library="ds2", parent="ds2",
                    visibility_of="ds2", groups=["ds10"]),
        "ds5": dict(kind="document-folder", library="ds1", parent="ds1", groups=["ds10"]),
        "ds6": dict(kind="file", owner="person"),
        "ds7": dict(kind="file", owner="other"),
        "ds8": dict(kind="module", name="files", on=True),
        "ds9": dict(kind="module", name="board", on=True),
        "ds11": dict(kind="word", word="files.browse", bound="files.browse", aliases="catalogue"),
        "ds12": dict(kind="grant", to="ds9", words="files.browse", where="place",
                     by="issuer", only="library:ds1"),
        "ds13": dict(kind="post", groups=["ds10"]),
        "ds14": dict(kind="post", groups=["elsewhere"]),
        "ds15": dict(kind="file", attached_to="ds13"),
        "ds16": dict(kind="file", attached_to="ds14"),
    }
    k.state = SimpleNamespace(things=facts, get=lambda t, key, default=None: facts.get(t, {}).get(key, default))
    k.shown = lambda person, t: (
        dict(facts[t], id=t, rev=1) if t in facts and not facts[t].get("hidden") else None)
    k.groups_of = lambda t: facts.get(t, {}).get("groups", ["place"])
    k.things = lambda kind: [t for t, row in facts.items() if row.get("kind") == kind]
    k.own = lambda person, t: facts.get(t, {}).get("owner") == person
    k.place, k.lock, k.seen = "place", threading.RLock(), {}
    k.up = lambda group: [group, "place"]
    k.find_entry = lambda word, group=None: "ds11"
    k._may_person = lambda person, *args: person == "issuer"
    k.source = lambda entry: ("module", "files")
    k.module_named = lambda name: "ds8"
    k.outside_marks = lambda person, rows: None
    k.step = lambda actor, line, mode: dict(
        rows=[k.shown(actor.person, t) for t in k.things(L.parse(line).words)
              if k.shown(actor.person, t)], text="unfiltered foreign secret")
    calls = []
    def call(mid, word, args, caller):
        reading = k.module_see(mid, caller, "rows document-folder")
        calls.append((word, caller, reading))
        return dict(rows=reading["rows"])
    k.modules = SimpleNamespace(running=lambda mid: True, call=call)
    viewer = Actor("person", "person", "person")
    board = Actor("ds9", viewer.person, "module", module="ds9", caller=viewer)
    return k, facts, viewer, board, calls


@pytest.mark.parametrize("word,target,values", [
    ("files.browse", None, dict(library="ds1")),
    ("files.folder", None, dict(library="ds1", parent="ds3", name="Notes")),
    ("files.store", "ds6", dict(library="ds1")),
    ("files.rename", "ds3", dict(name="Notes")),
    ("files.move", "ds3", dict(to="ds1")),
])
def test_complete_valid_selection(word, target, values):
    k, _, a, _, _ = memory_kernel()
    assert docs.selection(k, a, word, target, values) == "ds1"


@pytest.mark.parametrize("word,target,values", [
    ("files.browse", None, {}),
    ("files.browse", "ds1", dict(library="ds1")),
    ("files.browse", None, dict(library="ds1", parent="ds4")),
    ("files.folder", None, dict(library="ds1", parent="ds5")),
    ("files.folder", None, dict(library="ds1", within="ds2")),
    ("files.folder", None, dict(library="ds1", **{"in": "elsewhere"})),
    ("files.store", "ds7", dict(library="ds1")),
    ("files.store", "ds16", dict(library="ds1")),
    ("files.rename", "ds4", dict(library="ds1", name="Wrong")),
    ("files.move", "ds3", dict(to="ds4")),
])
def test_hidden_or_cross_library_selection_refuses(word, target, values):
    k, _, a, _, _ = memory_kernel()
    assert docs.selection(k, a, word, target, values) is None


def test_hidden_roots_parents_cycles_and_group_changes_fail_closed():
    k, facts, a, _, _ = memory_kernel()
    for tid, field, value in [("ds1", "hidden", True), ("ds3", "hidden", True),
                              ("ds3", "parent", "ds3"), ("ds3", "groups", ["elsewhere"])]:
        old = dict(facts[tid])
        facts[tid][field] = value
        assert docs.selection(k, a, "files.rename", "ds3", dict(name="No")) is None
        facts[tid] = old


def dispatch(k, actor, library, typed="files.browse"):
    return k.module_word(actor, L.parse(typed + " library=" + library),
                         dict(word="files.browse", bound="files.browse", id="ds11", word_kind="see"),
                         "place", "", None)


def test_outer_dispatch_filters_before_provider_and_preserves_shared_actor():
    k, _, _, board, calls = memory_kernel()
    out = dispatch(k, board, "ds1", "catalogue")
    assert [row["id"] for row in out["rows"]] == ["ds3"]
    assert calls[0][0] == "files.browse"
    assert calls[0][2]["text"] == ""
    assert not hasattr(board, "document_library")
    with pytest.raises(Refused, match="caller.*library"):
        dispatch(k, board, "ds2")
    assert len(calls) == 1


def test_overlapping_clauses_do_not_combine_and_expired_issuers_do_not_widen():
    k, facts, _, board, calls = memory_kernel()
    facts["ds17"] = dict(kind="grant", to="ds9", words="files.browse", where="elsewhere", by="issuer")
    facts["ds18"] = dict(kind="grant", to="ds9", words="files.browse", where="place", by="expired")
    facts["ds19"] = dict(kind="grant", to="ds9", words="files.browse", where="place",
                        by="issuer", only="library:ds2;fields:parent")
    with pytest.raises(Refused):
        dispatch(k, board, "ds2")
    assert not calls
    # Existing valid unscoped grants retain union semantics. Issuance must audit
    # them; a scoped grant is not a revocation of separately granted authority.
    facts["ds20"] = dict(kind="grant", to="ds9", words="files.browse", where="place", by="issuer")
    assert [r["id"] for r in dispatch(k, board, "ds2")["rows"]] == ["ds4"]


def test_each_module_identity_in_caller_chain_must_admit_same_library():
    k, facts, _, board, calls = memory_kernel()
    inner = Actor("inner", board.person, "module", module="inner", caller=board)
    facts["ds17"] = dict(kind="grant", to="inner", words="files.browse", where="place",
                        by="issuer", only="library:ds2")
    with pytest.raises(Refused):
        dispatch(k, inner, "ds1")
    with pytest.raises(Refused):
        dispatch(k, inner, "ds2")
    assert not calls


@pytest.mark.parametrize("line", ["look ds2", "rows file in=elsewhere", "rows post extra",
                                 "catalogue library=ds2", "rows grant"])
def test_provider_cannot_read_around_scoped_context(line):
    k, _, _, board, _ = memory_kernel()
    board.document_library, board.document_target = "ds1", None
    out = k.module_see("ds8", board, line)
    assert out["rows"] == [] and out.get("refused")


def test_file_and_post_reads_exclude_unrelated_or_hidden_data():
    k, facts, _, board, _ = memory_kernel()
    board.document_library, board.document_target = "ds1", "ds6"
    assert [r["id"] for r in k.module_see("ds8", board, "rows file")["rows"]] == ["ds6", "ds15"]
    assert [r["id"] for r in k.module_see("ds8", board, "rows post")["rows"]] == ["ds13"]
    facts["ds13"]["hidden"] = True
    assert [r["id"] for r in k.module_see("ds8", board, "rows file")["rows"]] == ["ds6"]
    facts["ds1"]["hidden"] = True
    assert not k.module_see("ds8", board, "rows file")["rows"]


@pytest.mark.parametrize("word,kind,target,values,allowed", [
    ("make", "document-folder", None, dict(kind="document-folder", library="ds1",
        parent="ds1", within="ds1", name="Notes"), True),
    ("make", "document-folder", None, dict(kind="document-folder", library="ds1",
        parent="ds4", within="ds1", name="Notes"), False),
    ("make", "document-entry", None, dict(kind="document-entry", library="ds1",
        parent="ds1", within="ds1", name="Notes", file="ds6"), True),
    ("make", "document-entry", None, dict(kind="document-entry", library="ds1",
        parent="ds1", within="ds1", name="Notes", file="ds7"), False),
    ("make", "post", None, dict(kind="post", text="bypass"), False),
    ("set", "document-folder", "ds3", dict(name="Notes"), True),
    ("set", "document-folder", "ds3", dict(parent="ds4"), False),
    ("set", "document-folder", "ds3", dict(within="ds2"), False),
    ("set", "document-folder", "ds3", dict(visibility_of="ds2"), False),
    ("set", "document-folder", "ds5", dict(name="Legacy"), False),
    ("set", "file", "ds6", dict(name="Changed"), False),
])
def test_provider_write_shape_and_caller_file_identity(word, kind, target, values, allowed):
    k, _, a, _, _ = memory_kernel()
    provider = Actor("ds8", a.person, "module", module="ds8", caller=a)
    assert docs.admits(k, provider, "ds1", word, kind, target, values, "ds10") == allowed


def test_existing_kind_field_and_unscoped_grants_retain_admission():
    k, facts, a, _, _ = memory_kernel()
    facts["ds21"] = dict(kind="word", word="set", bound="set")
    k.find_entry = lambda word, group=None: "ds21"
    facts["ds22"] = dict(kind="grant", to="ds8", words="set", where="place",
                        by="issuer", only="kind:note;fields:title")
    provider = Actor("ds8", a.person, "module", module="ds8", caller=a)
    k.reaches(provider, "set", "note", target="ds99", fields={"title": "Allowed"})
    with pytest.raises(Refused):
        k.reaches(provider, "set", "note", target="ds99", fields={"text": "No"})
    facts["ds23"] = dict(kind="grant", to="ds8", words="set", where="place", by="issuer")
    k.reaches(provider, "set", "note", target="ds99", fields={"text": "Existing broad grant"})
