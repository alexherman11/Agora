"""Offline tests for native_run_verify (a10179): a fake kernel, real folders under this worktree's scratch.

    python research/window-lab/test_native_run_verify.py

No process, desktop, socket or registry of this PC is read. Each case states a situation a browser or mail run
could meet and the verdict it must get: violation, unknown, or observed with its limits, never a pass.
"""
import os
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agora_tmp  # noqa: E402
import native_run_verify as nv  # noqa: E402

PROFILE_ARG = "--user-data-dir={root}\\profile\\EBWebView"


class FakeScope:
    def __init__(self, native):
        self.handle, self.native = "JOB", native

    def snapshot(self):
        if self.native.job_fails:
            raise RuntimeError("job membership list incomplete")
        pids = sorted(self.native.job)
        return {"pids": pids, "active": len(pids), "total": len(pids), "terminated": 0}


class FakeNative:
    """procs: pid -> {"image", "created", "cmd" (None: unreadable), "gone"}; job: pids in the job."""

    def __init__(self, root):
        self.root = root
        self.procs, self.job, self.job_fails = {}, set(), False
        self.desktops = {"Default": [(5000, True)]}           # one of Alex's own windows
        self.desktop_fails = set()
        self.tcp_rows, self.udp_rows, self.net_fails = [], [], False
        self.installs = {"uninstall-user": ["A"], "services": ["svc"]}
        self.io = {"total": 2, "active": 0, "terminated": 0, "read_ops": 3, "write_ops": 4, "other_ops": 0,
                   "read_bytes": 10, "write_bytes": 20, "other_bytes": 0}

    def add(self, pid, image, cmd="", job=False, created=None):
        self.procs[pid] = {"image": image, "created": created or pid * 10, "cmd": cmd}
        if job:
            self.job.add(pid)

    def processes(self):
        return [(pid, 1, p["image"]) for pid, p in self.procs.items()]

    def open(self, pid):
        if pid not in self.procs:
            raise OSError(None, "gone", None, 87)
        if self.procs[pid].get("denied"):
            raise OSError(None, "Access is denied", None, 5)
        return pid

    def close(self, h):
        pass

    def identity(self, h):
        p = self.procs[h]
        return (p["created"], "c:\\x\\" + p["image"])

    def in_job(self, h, job):
        return h in self.job

    def command_line(self, h):
        cmd = self.procs[h]["cmd"]
        if cmd is None:
            raise OSError("unreadable")
        return cmd

    def job_io(self, job):
        return dict(self.io)

    def desktop_window_owners(self, desk):
        if desk in self.desktop_fails:
            raise OSError(None, "Access is denied", None, 5)
        return list(self.desktops.get(desk, []))

    def tcp(self):
        if self.net_fails:
            raise OSError("table call failed (50)")
        return list(self.tcp_rows)

    def udp(self):
        return list(self.udp_rows)

    def install_records(self):
        return {k: (list(v) if isinstance(v, list) else dict(v)) for k, v in self.installs.items()}


class Case(unittest.TestCase):
    def setUp(self):
        self.root = Path(agora_tmp.directory("nrv-test-"))
        (self.root / "profile").mkdir()
        (self.root / "scratch").mkdir()
        (self.root / "repo").mkdir()
        (self.root / "repo" / "a.txt").write_text("unchanged", encoding="utf-8")
        self.n = FakeNative(self.root)
        self.scope = FakeScope(self.n)
        self.ours = PROFILE_ARG.format(root=self.root)
        # a fake family: host 100 (python), engine 101, renderer 102, all in the job
        self.n.add(100, "python.exe", "python host.py", job=True)
        self.n.add(101, "msedgewebview2.exe", "msedgewebview2.exe " + self.ours, job=True)
        self.n.add(102, "msedgewebview2.exe", "msedgewebview2.exe --type=renderer " + self.ours, job=True)
        # Alex's own Edge, outside the job, his own profile
        self.n.add(900, "msedge.exe", "msedge.exe --profile-directory=Default")
        self.n.desktops["agora-sandbox-t"] = [(101, True), (100, False)]

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def verifier(self, **run):
        spec = {"name": "t", "profile_roots": [str(self.root / "profile")],
                "scratch_roots": [str(self.root / "scratch")], "watched_roots": [str(self.root / "repo")],
                "explained": [100, 101, 102]}
        spec.update(run)
        return nv.Verifier(spec, self.scope, native=self.n)

    def whole(self, v, between=None):
        v.before()
        v.sample()
        if between:
            between()
        v.sample()
        v.after()
        return v.verdict()

    # -- the clean fake family: observed, with limits, never a pass
    def test_clean_family_is_observed_with_its_limits(self):
        r = self.whole(self.verifier(), lambda: (self.root / "profile" / "Cookies").write_bytes(b"x"))
        for k in ("family", "windows", "network", "writes"):
            self.assertEqual(r[k]["status"], "observed", (k, r[k]))
            self.assertTrue(r[k]["not_proven"], k)
        self.assertTrue(r["allow_interaction"])
        self.assertEqual(r["writes"]["evidence"]["owned"][str(self.root / "profile")]["added"], ["Cookies"])
        self.assertNotIn("pass", str({k: r[k]["status"] for k in ("family", "windows", "network", "writes")}))
        self.assertEqual([m["pid"] for m in r["family"]["evidence"]["members"]], [100, 101, 102])

    # -- family
    def test_engine_holding_our_profile_before_launch_is_a_reused_engine(self):
        self.n.add(700, "msedgewebview2.exe", "msedgewebview2.exe " + self.ours)
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "violation")
        self.assertIn("reused", " ".join(r["family"]["reasons"]))
        self.assertFalse(r["allow_interaction"])

    def test_out_of_job_engine_naming_our_profile_during_run(self):
        v = self.verifier()
        v.before()
        self.n.add(701, "msedgewebview2.exe", "msedgewebview2.exe --type=gpu-process " + self.ours)
        v.sample()
        v.after()
        r = v.verdict()
        self.assertEqual(r["family"]["status"], "violation")
        self.assertTrue(any("701" in x and "outside the job" in x for x in r["family"]["reasons"]))

    def test_sibling_folder_with_a_longer_name_is_not_our_profile(self):
        self.n.add(702, "msedge.exe", f"msedge.exe --user-data-dir={self.root}\\profile2")
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "observed", r["family"])

    def test_unreadable_engine_outside_is_unknown_not_clean(self):
        self.n.add(703, "msedgewebview2.exe", None)
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "unknown")
        self.assertFalse(r["allow_interaction"])

    def test_access_denied_engine_is_unknown_but_a_vanished_one_is_not(self):
        self.n.add(704, "msedge.exe", "x")
        self.n.procs[704]["denied"] = True
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "unknown")

    def test_incomplete_job_list_is_unknown(self):
        self.n.job_fails = True
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "unknown")
        self.assertIn("membership", " ".join(r["family"]["reasons"]))

    def test_unexplained_member_is_unknown(self):
        self.n.add(105, "cmd.exe", "cmd", job=True)
        r = self.whole(self.verifier())
        self.assertEqual(r["family"]["status"], "unknown")
        self.assertIn("nobody explained", " ".join(r["family"]["reasons"]))

    def test_engine_report_binds_browser_pid_and_effective_folder(self):
        good = {"browser_pid": 101, "user_data_folder": str(self.root / "profile" / "EBWebView"),
                "processes": [{"pid": 101, "kind": "browser"}, {"pid": 102, "kind": "renderer"}]}
        v = self.verifier(explained=[100], require_engine_report=True)
        v.engine_report = lambda: good
        self.assertEqual(self.whole(v)["family"]["status"], "observed")

    def test_engine_report_with_browser_outside_the_job(self):
        self.n.add(800, "msedgewebview2.exe", "msedgewebview2.exe --user-data-dir=c:\\elsewhere")
        v = self.verifier(require_engine_report=True)
        v.engine_report = lambda: {"browser_pid": 800, "user_data_folder": str(self.root / "profile"),
                                   "processes": []}
        r = self.whole(v)
        self.assertEqual(r["family"]["status"], "violation")
        self.assertIn("not in the job", " ".join(r["family"]["reasons"]))

    def test_engine_report_with_another_profile(self):
        v = self.verifier(require_engine_report=True)
        v.engine_report = lambda: {"browser_pid": 101, "user_data_folder": "C:\\Users\\x\\AppData\\Local\\y",
                                   "processes": []}
        self.assertEqual(self.whole(v)["family"]["status"], "violation")

    def test_required_engine_report_missing_is_unknown(self):
        r = self.whole(self.verifier(require_engine_report=True))
        self.assertEqual(r["family"]["status"], "unknown")

    def test_survivor_after_cleanup(self):
        v = self.verifier()
        v.before()
        v.sample()
        self.n.job.clear()                    # cleanup emptied the job, but an engine lives on outside it
        self.n.add(705, "msedgewebview2.exe", "msedgewebview2.exe " + self.ours)
        v.after()
        r = v.verdict()
        self.assertEqual(r["family"]["status"], "violation")
        self.assertIn("after cleanup", " ".join(r["family"]["reasons"]))

    def test_gate_before_interaction(self):
        v = self.verifier()
        v.before()
        g = v.gate()
        self.assertEqual(g["phase"], "gate")
        self.assertTrue(g["allow_interaction"], g)
        self.assertEqual(g["writes"]["status"], "unknown")
        self.n.add(706, "msedgewebview2.exe", "msedgewebview2.exe " + self.ours)
        self.assertFalse(v.gate()["allow_interaction"])

    def test_gate_with_no_before_refuses(self):
        self.assertFalse(self.verifier().gate()["allow_interaction"])

    def test_no_after_observation_is_unknown(self):
        v = self.verifier()
        v.before()
        v.sample()
        self.assertEqual(v.verdict()["family"]["status"], "unknown")

    # -- windows
    def test_job_window_on_default_desktop(self):
        self.n.desktops["Default"].append((102, True))
        r = self.whole(self.verifier())
        self.assertEqual(r["windows"]["status"], "violation")

    def test_default_desktop_unreadable_is_unknown(self):
        self.n.desktop_fails.add("Default")
        r = self.whole(self.verifier())
        self.assertEqual(r["windows"]["status"], "unknown")

    def test_alex_windows_are_counted_never_described(self):
        r = self.whole(self.verifier())
        ev = r["windows"]["evidence"]["Default"]
        self.assertEqual(ev, {"samples": 2, "max_ours": 0})

    # -- network
    def test_mail_fake_allows_no_network(self):
        self.n.tcp_rows = [(101, 5, "10.0.0.2", 50000, "142.250.0.1", 443)]
        r = self.whole(self.verifier())
        self.assertEqual(r["network"]["status"], "violation")

    def test_browser_allowlist_one_public_host(self):
        self.n.tcp_rows = [(101, 5, "10.0.0.2", 50000, "93.184.215.14", 443),
                           (101, 11, "0.0.0.0", 0, "0.0.0.0", 0)]
        r = self.whole(self.verifier(allow_remote=[["93.184.215.14", 443]]))
        self.assertEqual(r["network"]["status"], "observed", r["network"])
        self.assertIn("hostname", " ".join(r["network"]["not_proven"]))

    def test_second_host_is_a_violation_even_for_the_browser(self):
        self.n.tcp_rows = [(102, 5, "10.0.0.2", 50001, "203.0.113.9", 443)]
        r = self.whole(self.verifier(allow_remote=[["93.184.215.14", 443]]))
        self.assertEqual(r["network"]["status"], "violation")

    def test_listen_beyond_loopback_is_a_violation(self):
        self.n.tcp_rows = [(100, 2, "0.0.0.0", 9222, "0.0.0.0", 0)]
        r = self.whole(self.verifier(allow_loopback=True))
        self.assertEqual(r["network"]["status"], "violation")

    def test_loopback_devtools_when_allowed(self):
        self.n.tcp_rows = [(101, 2, "127.0.0.1", 9222, "0.0.0.0", 0), (100, 5, "127.0.0.1", 50002,
                                                                      "127.0.0.1", 9222),
                           (101, 5, "::1", 9223, "::1", 50003)]
        self.assertEqual(self.whole(self.verifier(allow_loopback=True))["network"]["status"], "observed")
        self.assertEqual(self.whole(self.verifier())["network"]["status"], "violation")

    def test_udp_beyond_loopback_is_unknown(self):
        self.n.udp_rows = [(101, "0.0.0.0", 5353)]
        r = self.whole(self.verifier())
        self.assertEqual(r["network"]["status"], "unknown")

    def test_other_processes_sockets_are_not_ours(self):
        self.n.tcp_rows = [(900, 5, "10.0.0.2", 50004, "198.51.100.1", 443)]
        self.assertEqual(self.whole(self.verifier())["network"]["status"], "observed")

    def test_socket_table_failure_is_unknown(self):
        self.n.net_fails = True
        self.assertEqual(self.whole(self.verifier())["network"]["status"], "unknown")

    def test_coverage_says_samples_and_interval(self):
        v = self.verifier()
        r = self.whole(v)
        self.assertEqual(r["coverage"]["samples"], 2)
        self.assertIn("largest gap", r["network"]["observed"])

    # -- writes
    def test_change_outside_the_run_roots_is_a_violation(self):
        r = self.whole(self.verifier(), lambda: (self.root / "repo" / "a.txt").write_text("changed!", "utf-8"))
        self.assertEqual(r["writes"]["status"], "violation")
        self.assertEqual(r["writes"]["evidence"]["watched"][str(self.root / "repo")]["paths"], ["a.txt"])

    def test_harness_receipts_are_excluded(self):
        (self.root / "repo" / "receipts").mkdir()
        v = self.verifier(exclude=[str(self.root / "repo" / "receipts")])
        r = self.whole(v, lambda: (self.root / "repo" / "receipts" / "r.json").write_text("{}", "utf-8"))
        self.assertEqual(r["writes"]["status"], "observed", r["writes"])

    def test_new_install_record(self):
        r = self.whole(self.verifier(), lambda: self.n.installs["services"].append("newsvc"))
        self.assertEqual(r["writes"]["status"], "violation")

    def test_install_records_unreadable_is_unknown(self):
        self.n.installs["services"] = {"unreadable": {"type": "PermissionError"}}
        self.assertEqual(self.whole(self.verifier())["writes"]["status"], "unknown")

    def test_too_many_files_is_unknown_not_partial(self):
        v = self.verifier()
        old = nv.MAX_FILES
        nv.MAX_FILES = 2
        try:
            for i in range(3):
                (self.root / "scratch" / f"f{i}").write_text("x", "utf-8")
            r = self.whole(v)
        finally:
            nv.MAX_FILES = old
        self.assertEqual(r["writes"]["status"], "unknown")
        self.assertIn("incomplete", " ".join(r["writes"]["reasons"]))

    def test_reparse_points_are_not_followed(self):
        target = self.root / "outside"
        target.mkdir()
        try:
            os.symlink(target, self.root / "scratch" / "link", target_is_directory=True)
        except OSError:
            self.skipTest("this account cannot make a symlink (no privilege change attempted)")
        snap = nv.snapshot_root(self.root / "scratch", hash_files=True)
        self.assertEqual(snap["reparse"], ["link"])

    def test_owned_contents_are_hashed_never_stored(self):
        (self.root / "profile" / "secret").write_text("mail body", "utf-8")
        snap = nv.snapshot_root(self.root / "profile", hash_files=True)
        self.assertNotIn("mail body", str(snap))
        self.assertEqual(len(snap["files"]["secret"][2]), 64)

    def test_job_io_missing_is_unknown(self):
        v = self.verifier()
        v.before()
        v.sample()
        self.n.job_io = lambda job: (_ for _ in ()).throw(OSError("denied"))
        v.after()
        self.assertEqual(v.verdict()["writes"]["status"], "unknown")

    # -- pure helpers
    def test_names_root(self):
        r = "C:\\a\\run\\profile"
        self.assertTrue(nv.names_root('x --user-data-dir="C:\\A\\run\\profile\\EBWebView"', [r]))
        self.assertTrue(nv.names_root("x --user-data-dir=c:/a/run/profile", [r]))
        self.assertFalse(nv.names_root("x --user-data-dir=C:\\a\\run\\profile2", [r]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
