"""Fixtures only: never invoke a host process inventory or open a window."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import kd_system
import process_read as p

PREFIXES = ["C:\\Agora\\state\\", "C:\\Agora\\.worktrees\\", "C:\\Temp\\kernel-shoot-"]


def proc(pid, parent=0, name="python.exe", born="10", memory=100, ticks=10_000_000):
    return dict(pid=pid, parent_pid=parent, name=name, born=born,
                working_set=memory, private_bytes=memory * 2, cpu_ticks=ticks)


class ProcessTests(unittest.TestCase):
    def test_groups_profile_precedence_and_privacy(self):
        raw = {"processes": [proc(1), proc(2, 1), proc(3, 2, "node.exe"),
                             proc(4, 0, "chrome.exe"), proc(5, 1, "msedge.exe"),
                             proc(6, 0, "chrome.exe"), proc(7, 0, "obs64.exe")],
               "profiles": [{"pid": 4, "born": "10", "profile": r"C:\Temp\kernel-shoot-abc"},
                            {"pid": 5, "born": "10", "profile": r"C:\Agora\state\edge-kdesk-abc"},
                            {"pid": 6, "born": "10", "profile": r"C:\Users\Alex\Chrome"}]}
        raw["processes"][0]["CommandLine"] = "must never escape"
        raw["processes"][0]["title"] = "private title"
        result = p.snapshot(raw, 1, PREFIXES)
        self.assertEqual([r["group"] for r in result["rows"]],
                         ["agora"] * 3 + ["agora-helper-chrome"] * 2 + ["other"] * 2)
        encoded = json.dumps(p.response(dict(result, at=1)))
        self.assertNotIn("must never escape", encoded)
        self.assertNotIn("private title", encoded)
        self.assertNotIn("Users", encoded)
        self.assertEqual([r["count"] for r in result["totals"]], [3, 2, 2])
        self.assertNotIn("profile", result["rows"][5])

    def test_profile_boundaries_normalization_and_pid_reuse(self):
        for path in [r"C:\Agora\state-other\profile", r"C:\Agora\state\..\personal",
                     r"C:\Temp\unrelated", r"state\relative"]:
            self.assertIsNone(p.helper_profile(path, PREFIXES))
        self.assertEqual(p.helper_profile("c:/agora/state/edge", PREFIXES), r"c:\agora\state\edge")
        raw = {"processes": [proc(1), proc(2, 1, "chrome.exe")],
               "profiles": [{"pid": 2, "born": "9", "profile": r"C:\Agora\state\edge"}]}
        self.assertEqual(p.snapshot(raw, 1, PREFIXES)["rows"][1]["group"], "agora")

    def test_tree_missing_parents_reused_parent_cycles_and_no_name_guessing(self):
        raw = {"processes": [proc(1, born="20"), proc(2, 1, born="10"), proc(3, 99),
                             proc(4, 5), proc(5, 4), proc(6, 0, "python.exe")]}
        result = p.snapshot(raw, 1, PREFIXES)
        self.assertEqual([r["group"] for r in result["rows"]], ["agora"] + ["other"] * 5)

    def test_cpu_machine_percentage_new_pid_and_reset(self):
        old = {1: proc(1)}
        raw = {"processes": [proc(1, ticks=50_000_000), proc(2)]}
        rows = p.snapshot(raw, 1, [], old, elapsed=2, cpus=4)["rows"]
        self.assertEqual(rows[0]["cpu_pct"], 50)
        self.assertIsNone(rows[1]["cpu_pct"])
        for new in [proc(1, born="11"), proc(1, ticks=0)]:
            self.assertIsNone(p.snapshot({"processes": [new]}, 1, [], old, 2, 4)["rows"][0]["cpu_pct"])

    def test_totals_cover_more_than_top_30_and_unknown_counters(self):
        raw = {"processes": [proc(n, 1, memory=n) for n in range(1, 41)]}
        raw["processes"][0]["private_bytes"] = None
        result = p.snapshot(raw, 1, [])
        self.assertEqual(len(result["rows"]), 30)
        self.assertEqual([r["pid"] for r in result["rows"]], list(range(40, 10, -1)))
        total = result["totals"][0]
        self.assertEqual(total["count"], 40)
        self.assertEqual(total["working_set"], sum(range(1, 41)))
        self.assertEqual(total["private_bytes_unknown"], 1)
        self.assertEqual(total["cpu_pct_unknown"], 40)
        self.assertIn("1 unknown memory counters", p.agora_memory(result)["detail"])

    def test_collect_is_hidden_bounded_and_receives_only_prefixes(self):
        with patch.object(p.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"processes":[]}', "")) as run:
            self.assertEqual(p.collect(PREFIXES), {"processes": []})
        args, kw = run.call_args
        self.assertEqual(args[0][0], "powershell.exe")
        self.assertEqual(kw["timeout"], 8)
        self.assertEqual(kw["creationflags"], 0x08000000)
        self.assertEqual(json.loads(kw["input"]), {"prefixes": PREFIXES})

    def test_failure_clears_old_data_without_leaking_errors_or_retrying(self):
        reader = p.Reader(1, [])
        with patch.object(p, "collect", return_value={"processes": [proc(1)]}):
            reader.sample()
        self.assertIn("totals", reader.last)
        with patch.object(p, "collect", side_effect=OSError("secret command line")) as collect:
            reader.sample()
            collect.assert_called_once()
        self.assertIsNone(reader.previous)
        self.assertEqual(p.agora_memory(reader.last)["value"], "unavailable")
        self.assertNotIn("secret", json.dumps(p.response(reader.last)))
        self.assertEqual(p.response(reader.last)["rows"], [])

    def test_system_words_use_cache_and_headless_never_collects(self):
        with patch.object(kd_system, "HEADLESS", True), patch.object(p, "collect", side_effect=AssertionError("OS probe")):
            system = kd_system.System()
            system.hello({"home": str(Path.cwd() / ".tmp/world/modules/system")})
            answer = system.call({"word": "system.processes"})
            self.assertEqual(len(answer["rows"]), 3)
            now = system.call({"word": "system.now"})
            self.assertEqual(next(r for r in now["rows"] if r["key"] == "agora")["value"], "0.00 GB")
            words = {w["word"]: w for w in system.offer()}
            self.assertEqual(words["system.processes"]["kind"], "see")
            self.assertIn("profile", words["system.processes"]["help"])
            self.assertIn("system.processes", words["system.now"]["help"])

    def test_powershell_collector_with_fixture_cim_only(self):
        # Shadow the cmdlet before loading the production script. No OS inventory.
        fixture = r'''
function Get-CimInstance {
    param([string]$Query)
    if ($Query -eq 'SELECT Name,ProcessId,ParentProcessId,CreationDate,WorkingSetSize,PrivatePageCount,KernelModeTime,UserModeTime FROM Win32_Process') {
        [pscustomobject]@{Name='chrome.exe'; ProcessId=42; ParentProcessId=1
            CreationDate=[datetime]'2026-11-06T12:00:00Z'; WorkingSetSize=123
            PrivatePageCount=456; KernelModeTime=100; UserModeTime=200}
    } elseif ($Query.StartsWith('SELECT ProcessId,CreationDate,CommandLine FROM Win32_Process WHERE ') -and
              $Query.Contains("(Name='chrome.exe' OR Name='msedge.exe')") -and
              $Query.Contains("CommandLine LIKE '%--user-data-dir=C:\\Agora\\state\\%'")) {
        foreach ($line in @(
            'chrome --user-data-dir="C:\Agora\state\test profile" --secret=never-output',
            'chrome "--user-data-dir=C:\Agora\state\test profile" --secret=never-output',
            'chrome --user-data-dir C:\Agora\state\plain --secret=never-output',
            'chrome --user-data-dir=C:\Agora\state\..\personal --secret=never-output'
        )) {
            [pscustomobject]@{ProcessId=42; CreationDate=[datetime]'2026-11-06T12:00:00Z'; CommandLine=$line}
        }
    } else { throw 'Unexpected query' }
}
'''
        script = str(Path(p.__file__).with_suffix(".ps1")).replace("'", "''")
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                                 fixture + "\n& '" + script + "'"],
                                input=json.dumps({"prefixes": PREFIXES}), capture_output=True,
                                encoding="utf-8", timeout=15, creationflags=0x08000000)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["processes"][0]["cpu_ticks"], 300)
        self.assertEqual(len(output["profiles"]), 3)
        self.assertEqual(output["profiles"][0]["profile"], r"C:\Agora\state\test profile")
        self.assertNotIn("never-output", result.stdout)
        self.assertNotIn("personal", result.stdout)


if __name__ == "__main__":
    unittest.main()
