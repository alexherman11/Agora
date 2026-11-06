"""Offline fixtures only. Never inspect or terminate a host process."""
import copy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import kd_system
import process_helpers as h
import process_read as p
from test_process_read import PREFIXES, proc


@pytest.fixture(autouse=True)
def no_real_process_access(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("Only fake process inventories and handles are allowed")
    monkeypatch.setattr(p, "collect", refuse)
    monkeypatch.setattr(h.WindowsProcesses, "__init__", refuse)


def inventory():
    return {"processes": [proc(1), proc(2, 1, "chrome.exe"), proc(3, 2, "chrome.exe"),
                          proc(4, 3, "chrome.exe"), proc(5, 1, "chrome.exe"),
                          proc(6, 0, "obs64.exe"), proc(7, 1, "python.exe")],
            "profiles": [{"pid": 2, "born": "10", "profile": r"C:\Temp\kernel-shoot-abc"},
                         {"pid": 5, "born": "10", "profile": r"C:\Users\Alex\Chrome"}]}


class Backend:
    def __init__(self):
        self.opened, self.ended, self.closed = [], [], []

    def open(self, row):
        self.opened.append(row["pid"])
        return row["pid"] + 1000  # handles, deliberately not PIDs

    def terminate(self, handle):
        self.ended.append(handle)

    def exited(self, handle):
        return handle in self.ended

    def close(self, handle):
        self.closed.append(handle)


def run(raw=None, dry=False, backend=None, **kwargs):
    collector = Mock(return_value=raw if raw is not None else inventory())
    result = h.end_helpers(PREFIXES, dry=dry, collect=collector, backend=backend, **kwargs)
    collector.assert_called_once_with(PREFIXES, timeout=5)
    return result


def test_dry_lists_only_verified_full_tree_without_handles_or_effects():
    backend = Backend()
    out = run(dry=True, backend=backend)
    assert [r["pid"] for r in out["rows"]] == [2, 3, 4]
    assert all(r["outcome"] == "would end" and r["released_working_set"] == 0 for r in out["rows"])
    assert not backend.opened and not backend.ended and not out["external"]
    assert "Users" not in str(out)


def test_full_tree_root_first_and_only_verified_handles_terminated():
    backend = Backend()
    out = run(backend=backend)
    assert backend.opened == [2, 3, 4]
    assert backend.ended == backend.closed == [1002, 1003, 1004]
    assert all(r["outcome"] == "ended" for r in out["rows"])
    assert sum(r["released_working_set"] for r in out["rows"]) == 300
    assert "not measured physical RAM" in out["text"]

def test_multiple_profiles_include_whole_trees_and_match_the_reading_group():
    raw = inventory()
    raw["processes"].extend([proc(10, 2, "crashpad_handler.exe"),
                             proc(11, 10, "utility.exe"),
                             proc(12, 0, "msedge.exe"), proc(13, 12, "msedge.exe"),
                             proc(14, 0, "crashpad_handler.exe"),
                             proc(15, 0, "python.exe")])
    raw["profiles"].extend([{"pid": 12, "born": "10", "profile": r"C:\Agora\.worktrees\fixture\profile"},
                             # A non-browser root cannot qualify from a supplied profile alone.
                             {"pid": 15, "born": "10", "profile": r"C:\Temp\kernel-shoot-fake"}])
    backend = Backend()
    out = run(raw, backend=backend)
    selected = {r["pid"] for r in p.snapshot(raw, 1, PREFIXES)["rows"]
                if r["group"] == "agora-helper-chrome"}
    assert {r["pid"] for r in out["rows"]} == selected == {2, 3, 4, 10, 11, 12, 13}
    assert backend.ended.index(1002) < backend.ended.index(1010) < backend.ended.index(1011)
    assert backend.ended.index(1012) < backend.ended.index(1013)
    assert all(r["outcome"] == "ended" for r in out["rows"])
    assert next(r["profile"] for r in out["rows"] if r["pid"] == 11) == r"C:\Temp\kernel-shoot-abc"


def test_an_explicit_unowned_profile_does_not_inherit_helper_ownership():
    raw = inventory()
    raw["processes"][4]["parent_pid"] = 2
    raw["processes"].append(proc(8, 5, "chrome.exe"))
    assert {r["pid"] for r in run(raw, dry=True)["rows"]} == {2, 3, 4}



def test_more_than_top_thirty_are_included_and_profile_boundaries_refuse():
    raw = inventory()
    raw["processes"].extend(proc(i, 2, "chrome.exe") for i in range(10, 60))
    assert len(run(raw, dry=True)["rows"]) == 53
    for folder in [r"C:\Temp\kernel-shoot-abc\..\personal", r"C:\Agora\state-else\browser",
                   r"C:\Users\Alex\Chrome", r"\Temp\kernel-shoot-abc", "relative"]:
        bad = copy.deepcopy(raw)
        bad["profiles"][0]["profile"] = folder
        backend = Backend()
        assert not run(bad, backend=backend)["rows"]
        assert not backend.opened


def test_inventory_access_denial_does_not_fallback_or_leak_details():
    collector = Mock(side_effect=PermissionError("private information"))
    backend = Backend()
    out = h.end_helpers(PREFIXES, collect=collector, backend=backend)
    collector.assert_called_once()
    assert "refused" in out and "private information" not in str(out)
    assert not backend.opened


@pytest.mark.parametrize("error", [h.ProcessChanged, PermissionError])
def test_identity_or_access_failure_preflights_whole_tree_before_acting(error):
    backend = Backend()
    def fail(row):
        if row["pid"] == 3:
            raise error("secret")
        return 1002
    backend.open = fail
    out = run(backend=backend)
    assert "nothing ended" in out["refused"]
    assert not backend.ended and backend.closed == [1002]
    assert "secret" not in str(out)


def test_partial_failure_is_reported_and_not_called_no_effect():
    backend = Backend()
    terminate = backend.terminate
    def fail(handle):
        if handle == 1003:
            raise PermissionError("secret")
        terminate(handle)
    backend.terminate = fail
    out = run(backend=backend)
    assert "refused" not in out
    assert [r["outcome"] for r in out["rows"]] == ["ended", "denied; not ended", "ended"]
    assert sum(r["released_working_set"] for r in out["rows"]) == 200
    assert backend.closed == [1002, 1003, 1004]


def test_unconfirmed_exit_is_bounded_and_never_claims_freed_memory():
    backend = Backend()
    backend.exited = lambda handle: False
    times = iter([0, 2])
    out = run(backend=backend, clock=lambda: next(times))
    assert all(r["outcome"] == "exit pending" and r["released_working_set"] == 0 for r in out["rows"])
    assert backend.closed == [1002, 1003, 1004]


def test_native_identity_check_uses_birth_time_and_the_same_handle():
    backend = h.WindowsProcesses.__new__(h.WindowsProcesses)
    born = 133000000000000007
    def stamps(handle, creation, *others):
        assert handle == 9876
        creation._obj.dwHighDateTime = born >> 32
        creation._obj.dwLowDateTime = born & 0xFFFFFFFF
        return True
    backend.api = SimpleNamespace(OpenProcess=Mock(return_value=9876),
                                  GetProcessTimes=Mock(side_effect=stamps),
                                  CloseHandle=Mock(), WaitForSingleObject=Mock(return_value=258),
                                  TerminateProcess=Mock(return_value=True))
    row = proc(42, born=str((born // 10) * 10 + 504911232000000000))
    handle = backend.open(row)
    backend.terminate(handle)
    backend.api.TerminateProcess.assert_called_once_with(9876, 1)
    row["born"] = str(int(row["born"]) + 10)
    with pytest.raises(h.ProcessChanged):
        backend.open(row)
    backend.api.CloseHandle.assert_called_once_with(9876)
    backend.api.TerminateProcess.assert_called_once()


def test_word_rejects_selectors_headless_has_no_effect_and_overlaps_refuse():
    system = kd_system.System()
    with patch.object(h, "end_helpers", side_effect=AssertionError("must not act")):
        with patch.object(kd_system, "HEADLESS", True):
            assert "Headless" in system.call({"word": "system.end-helpers"})["text"]
        with patch.object(kd_system, "HEADLESS", False):
            for args in [{"kv": {"pid": "3"}}, {"words": "chrome.exe"}, {"target": "3"},
                         {"kv": {"profile": "C:\\Temp\\kernel-shoot-a"}}, {"kv": {"dry": "no"}}]:
                assert "refused" in system.call({"word": "system.end-helpers", "args": args})
            system.helpers_lock.acquire()
            try:
                assert "already running" in system.call({"word": "system.end-helpers"})["refused"]
            finally:
                system.helpers_lock.release()


@pytest.fixture
def world_dir():
    # The repository scratch helper uses inherited ACLs; pytest's owner-only
    # Windows temp folders cannot be read by a sandboxed worker.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "kernel-lab"))
    from kernel import scratch
    with scratch.TemporaryDirectory(prefix="helper-word-") as folder:
        yield Path(folder) / "world"


def test_kernel_admits_only_stewards_including_owner(world_dir):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "kernel-lab"))
    from kernel.kernel import Actor, Kernel
    kernel = Kernel(world_dir, {"tag": "dk", "name": "fixture",
                                      "steward": {"account": "owner", "name": "Owner"}})
    owner = kernel.accounts["owner"]
    steward = kernel.join("steward", "Steward", invite={"admitted": "steward"})["person"]
    member = kernel.join("member", "Member", invite={"admitted": "member"})["person"]
    assert kernel.run(Actor(owner, owner, "person"), f"look {steward}; role {steward} leader")["ok"]
    made = kernel.run(Actor(owner, owner, "person"), """module system run='["fixture"]' grants="" """)
    assert made["ok"], made
    module = kernel.module_named("system")
    system = kd_system.System()
    kernel.on_offer(module, system.offer())
    called = []
    def call(mid, word, args, caller):
        called.append(caller.person)
        return {"text": "fixture; no OS effects", "rows": []}
    kernel.modules = SimpleNamespace(call=call, running=lambda mid: True,
                                     reconcile=lambda: None, deliver=lambda h: None)
    for person in [owner, steward]:
        out = kernel.run(Actor(person, person, "person"), "system.end-helpers dry=yes")
        assert out["ok"], out
        assert not out["records"]
    for line in ["system.end-helpers", "system.end-helpers dry=yes"]:
        out = kernel.run(Actor(member, member, "person"), line)
        assert not out["ok"] and "steward" in out["text"]
    assert called == [owner, steward]
    # Actual cleanup is an external receipt; a dry read above is not.
    kernel.modules.call = lambda *args, **kwargs: {"external": True, "text": "fixture ended", "rows": []}
    out = kernel.run(Actor(owner, owner, "person"), "system.end-helpers")
    assert out["ok"] and len(out["records"]) == 1
    undo = kernel.run(Actor(owner, owner, "person"), "undo " + out["records"][0])
    assert not undo["ok"]
