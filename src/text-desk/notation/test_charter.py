# health: room test
# ruff: noqa: E402 -- transport and lab imports follow their explicit path bootstrap
"""Live charter changes reach stub starts; no inference, credentials or windows."""

import io
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
sys.path.insert(0, str(HERE.parents[1] / "codex"))
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import agora_tmp
import charter
import codex_resident
import codex_worker
import house
import roomworld
import workshop


class CharterTests(unittest.TestCase):
    def setUp(self):
        self.d, self.rooms = roomworld.build(say=False)
        self.w = self.d.world
        self.root = Path(agora_tmp.directory("charter-test-"))
        self.calls = []
        self.note = self.create(
            "note", "Live rules", role="agent-charter", text="- Keep the sandbox hidden."
        )
        self.card = self.create("task", "Stub charter worker", worker_provider="claude")
        self.corner = self.w.root
        self.w.nodes[self.corner].setdefault("props", {}).update(actor="pike", role="resident")
        self.h = SimpleNamespace(
            dir=self.root / "state",
            load=lambda: self.w,
            act=self.act,
            world="roomworld",
            fake=True,
            claude="claude.exe",
        )
        self.h.dir.mkdir()
        self.tree = self.root / "tree"
        self.tree.mkdir()
        (self.tree / "AGENTS.md").write_text(
            "# Agora\n\nUnrelated existing rules.\n", encoding="utf-8"
        )

    def act(self, actor, line, **kwargs):
        from desk import split_batch

        w = self.w
        w.me = actor
        if actor not in self.d._per:
            self.d._per[actor] = ({}, {w.root}, len(w.events))
        self.d.seen, self.d.open, self.d.last_event_seen = self.d._per[actor]
        self.d._window = ""
        out = []
        for part in split_batch(line):
            r = self.d.dispatch("desk", {"line": part, "whole": True})
            answer = r.get("text", r.get("error", ""))
            if (
                r.get("error")
                or "MISS " in answer
                or "ERR " in answer
                or "refused" in answer.lower()
            ):
                raise AssertionError(answer)
            out.append(answer)
        self.calls.append((actor, line))
        return "\n".join(out)

    def create(self, kind, title, **props):
        args = " ".join(f"{k}={charter.q(v)}" for k, v in props.items())
        out = self.act(
            "pike",
            f"look {self.w.root}; do create {self.w.root} kind={kind} "
            f"title={charter.q(title)} {args}",
        )
        import re

        return re.findall(r"created ([af]\d+)", out)[-1]

    def edit(self, text):
        self.act("pike", f"read {self.note} :3; do rewrite {self.note} text={charter.q(text)}")

    def start_worker(self, provider="claude"):
        subject = self.w.subjects[self.w.nodes[self.card]["subject"]]
        if subject["props"].get("worker_provider") != provider:
            self.act("pike", f"read {self.card} :1; do prop {self.card} worker_provider={provider}")
        # A different provider is a different saved worker; fixtures have no model session.
        state = self.h.dir / f"worker-{self.card}" / "state.json"
        if state.exists():
            data = json.loads(state.read_text(encoding="utf-8"))
            data.pop("session_provider", None)
            state.write_text(json.dumps(data), encoding="utf-8")
        wk = workshop.Worker(self.h, self.card, self.tree, "worker/test", "jeff")
        proc = MagicMock()
        proc.stdout = io.StringIO("")
        proc.pid = 500
        with (
            patch.object(workshop.subprocess, "Popen", return_value=proc) as popen,
            patch.object(workshop.threading, "Thread"),
        ):
            wk.start("test-model", "roomworld", None)
        self.addCleanup(lambda: popen.call_args.kwargs["stderr"].close())
        return wk, popen.call_args.args[0]

    def test_edited_rule_in_both_worker_prompts(self):
        for provider in ("claude", "codex"):
            self.edit(f"- A newly edited rule for {provider} must be here.")
            wk, cmd = self.start_worker(provider)
            text = (
                cmd[cmd.index("--append-system-prompt") + 1]
                if provider == "claude"
                else (wk.dir / "worker-prompt.txt").read_text(encoding="utf-8")
            )
            self.assertIn(f"A newly edited rule for {provider}", text)
            self.assertIn("Unrelated existing rules", text)
            self.assertTrue(
                any(
                    "rules injected (" in line and "as of event e" in line for _, line in self.calls
                )
            )
            if provider == "codex":
                mcp = wk.dir / "mcp.json"
                params = codex_worker.thread_parameters(self.tree, "test-model", text, mcp)
                self.assertEqual(text, params["developerInstructions"])

    def test_missing_or_empty_note_does_not_break_worker_start(self):
        self.edit("")
        for missing in (False, True):
            if missing:
                # Remove only from this in-memory fixture.
                self.w.nodes.pop(self.note)
            for provider in ("claude", "codex"):
                wk, cmd = self.start_worker(provider)
                text = (
                    cmd[cmd.index("--append-system-prompt") + 1]
                    if provider == "claude"
                    else (wk.dir / "worker-prompt.txt").read_text(encoding="utf-8")
                )
                lines = [
                    line for line in text.splitlines() if line.startswith("charter: not read:")
                ]
                self.assertEqual(1, len(lines))
                self.assertIn("note missing" if missing else "note empty", lines[0])
                self.assertIn("starting without standing rules", lines[0])
        self.assertTrue(any("rules unavailable" in line for _, line in self.calls))

    def test_worker_plain_resume_keeps_charter_without_start_read(self):
        wk, _ = self.start_worker()
        wk.state["session"] = "existing-session"
        wk.save()
        self.edit("- Changed while the worker was resting.")
        self.calls.clear()
        _, cmd = self.start_worker()
        text = cmd[cmd.index("--append-system-prompt") + 1]
        self.assertIn("Keep the sandbox hidden", text)
        self.assertNotIn("Changed while", text)
        self.assertFalse(any("charter read (reason: start)" in line for _, line in self.calls))
        self.assertTrue(any("cached charter" in line for _, line in self.calls))

    def test_generated_block_preserves_uncommitted_surroundings(self):
        original = "# Agora\r\n\r\nAlex's uncommitted text.\r\n"
        block = charter.generated(self.w)
        first = charter.replace_block(original, block)
        self.assertIn("Alex's uncommitted text.\r\n", first)
        self.assertEqual(first, charter.replace_block(first, block))
        self.edit("- New single-source rule.")
        second = charter.replace_block(first, charter.generated(self.w))
        self.assertIn("New single-source rule", second)
        self.assertNotIn("Keep the sandbox", second)
        self.assertIn("Alex's uncommitted text.\r\n", second)
        with self.assertRaises(ValueError):
            charter.replace_block(original + charter.BEGIN, block)

    def test_large_charter_is_bounded_and_linked(self):
        self.edit("\n".join(f"- Rule {i}: " + ("detail " * 40) for i in range(30)))
        reading = charter.read(self.w)
        self.assertLessEqual(reading.words, 500)
        self.assertIn(f"read {self.note} :3", reading.text)
        self.assertIn("bounded extract", reading.warning)
        self.assertLessEqual(len(charter.read(self.w, inline=True).text.split()), 500)

    def test_no_generated_stale_rule_in_worker_prompt(self):
        block = charter.generated(self.w)
        (self.tree / "AGENTS.md").write_text(
            charter.replace_block("# Agora\n", block), encoding="utf-8"
        )
        self.edit("- The latest live rule.")
        _, cmd = self.start_worker()
        text = cmd[cmd.index("--append-system-prompt") + 1]
        self.assertIn("latest live rule", text)
        self.assertNotIn("Keep the sandbox hidden", text)
        self.assertEqual(1, text.count("## Alex's standing rules"))

    def test_fresh_resident_reads_once_plain_resume_does_not(self):
        r = house.Resident(self.h, self.corner)
        proc = MagicMock(pid=501)
        with (
            patch.object(house.subprocess, "Popen", return_value=proc) as popen,
            patch.object(house.threading, "Thread"),
        ):
            r.start("test-model")
            cmd = popen.call_args.args[0]
            self.addCleanup(lambda f=popen.call_args.kwargs["stderr"]: f.close())
            self.assertIn("Keep the sandbox", cmd[cmd.index("--system-prompt") + 1])
            count = len(self.calls)
            r.state["session"] = "kept-session"
            r.start("test-model")
            self.addCleanup(lambda f=popen.call_args.kwargs["stderr"]: f.close())
            self.assertEqual(count, len(self.calls))
            self.assertIn("--resume", popen.call_args.args[0])

    def test_start_reads_and_compaction_reread(self):
        extra = self.create("note", "Extra start note", text="Read me on fresh memory.")
        self.w.nodes[self.corner]["props"]["start"] = f"read {self.note} :3; read {extra} :3"
        text = charter.collect(self.w, self.act, self.corner, "pike", "start")
        self.assertIn("Read me on fresh memory", text)
        self.edit("- Changed after compaction.")
        refreshed = charter.collect(self.w, self.act, self.corner, "pike", "compaction")
        self.assertIn("Changed after compaction", refreshed)
        self.assertIn("Read me on fresh memory", refreshed)
        self.assertTrue(any("reason: compaction" in line for _, line in self.calls))

    def test_start_cannot_run_mutations(self):
        self.w.nodes[self.corner]["props"]["start"] = f"do rewrite {self.note} text=bad"
        text = charter.collect(self.w, self.act, self.corner, "pike", "start")
        self.assertIn("skipped a non-read", text)
        self.assertIn("Keep the sandbox", charter.read(self.w).text)
        self.w.nodes[self.corner]["props"]["start"] = (
            f"read {self.note} :3\ndo rewrite {self.note} text=bad"
        )
        text = charter.collect(self.w, self.act, self.corner, "pike", "compaction")
        self.assertIn("skipped a non-read", text)
        self.assertIn("Keep the sandbox", charter.read(self.w).text)

    def test_claude_compaction_hook_rereads_live_note(self):
        settings = charter.claude_hook("python.exe", "roomworld", self.card, "worker")
        hook = settings["hooks"]["SessionStart"][0]
        self.assertEqual("compact", hook["matcher"])
        self.assertIn("--hook", hook["hooks"][0]["command"])
        # Exercise hook entrypoint, not merely its command string.
        self.edit("- Changed while Claude was working.")
        args = [
            "charter.py",
            "--world",
            "roomworld",
            "--target",
            self.card,
            "--actor",
            "worker",
            "--hook",
        ]
        with (
            patch.object(sys, "argv", args),
            patch.object(
                charter,
                "live_reading",
                side_effect=lambda *a: charter.read(self.w),
            ),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            charter.main()
        data = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual("SessionStart", data["hookEventName"])
        self.assertIn("Changed while Claude", data["additionalContext"])

    def test_codex_compaction_developer_injection_and_duplicate_signal(self):
        self.edit("- Fresh at Codex compaction.")
        args = SimpleNamespace(world="roomworld", target=self.card, actor="worker")
        emitted = []
        client = MagicMock()
        client.request.return_value.model_dump.return_value = {
            "rateLimits": {"limitId": "codex", "primary": {"usedPercent": 12}},
            "rateLimitsByLimitId": {},
        }
        notifications = [
            ("item/completed", {"item": {"type": "contextCompaction", "id": "c1"}}),
            ("thread/compacted", {}),
            ("turn/completed", {"turn": {"status": "completed"}}),
        ]
        client.next_turn_notification.side_effect = [
            SimpleNamespace(method=method, payload=SimpleNamespace(params=data))
            for method, data in notifications
        ]
        with patch.object(
            charter,
            "live_reading",
            side_effect=lambda *a: charter.read(self.w),
        ):
            ok = codex_resident.receive(
                client,
                "t1",
                emitted.append,
                lambda: codex_resident.refresh_charter(client, "thread1", args, emitted.append),
            )
        self.assertTrue(ok)
        self.assertEqual(
            ["thread/inject_items", "account/rateLimits/read"],
            [call.args[0] for call in client.request.call_args_list],
        )
        _, data = client.request.call_args_list[0].args
        self.assertEqual("developer", data["items"][0]["role"])
        self.assertIn("Fresh at Codex compaction", data["items"][0]["content"][0]["text"])
        self.assertEqual(1, sum(e.get("subtype") == "compact_boundary" for e in emitted))
        self.assertTrue(any(e.get("subtype") == "charter_read" for e in emitted))
        self.assertTrue(any(
            e.get("method") == "account/rateLimits/read"
            and e["data"]["rateLimits"]["primary"]["usedPercent"] == 12
            for e in emitted
        ))

    def test_mirror_updates_file_and_carried_note_without_churn(self):
        carried = self.create("note", "AGENTS.md", text="# Agora\n\nCarried human edits.\n")
        path = self.tree / "AGENTS.md"
        state = {}
        charter.sync(self.w, self.act, path, state)
        text = path.read_text(encoding="utf-8")
        self.assertIn(charter.BEGIN, text)
        body = self.w.subjects[self.w.nodes[carried]["subject"]]["text"]
        self.assertIn("Carried human edits.", body)
        self.assertIn(charter.BEGIN, body)
        calls = len(self.calls)
        charter.sync(self.w, self.act, path, state)
        self.assertEqual(calls, len(self.calls))
        charter.sync(self.w, self.act, path, {})  # restart must not churn events
        self.assertEqual(calls, len(self.calls))
        self.edit("- Next revision reaches both mirrors.")
        charter.sync(self.w, self.act, path, state)
        self.assertIn("Next revision", path.read_text(encoding="utf-8"))
        self.assertIn("Next revision", self.w.subjects[self.w.nodes[carried]["subject"]]["text"])

    def test_rule_edit_updates_both_mirrors_without_knocks_or_session_nudges(self):
        carried = self.create("note", "AGENTS.md", text="# Agora\n\nHuman text.\n")
        path = self.tree / "AGENTS.md"
        state = {}
        charter.sync(self.w, self.act, path, state)
        wk, _ = self.start_worker()
        wk.state["session"] = "resting-worker-session"
        wk.save()
        resident = house.Resident(self.h, self.corner)
        resident.state.update(
            session="resting-resident-session", charter_text=charter.read(self.w).text,
            cursor=len(self.w.events), at_rest=True,
        )
        resident.save()
        old_worker = wk.state["charter_text"]
        old_resident = resident.state["charter_text"]
        routing = house.House.__new__(house.House)
        routing.dir, routing.world = self.h.dir, self.h.world
        routing.load, routing.act = self.h.load, self.act
        routing.residents = {self.corner: resident}
        corners = {self.corner: self.w.nodes[self.corner]}
        routing.record_knocks(self.w, corners)  # initialize the real knock cursor
        start = len(self.w.events)
        wk.state["cursor"] = start
        self.calls.clear()
        with (
            patch.object(house.Resident, "start") as resident_start,
            patch.object(house.Resident, "send") as resident_send,
            patch.object(type(wk), "start") as worker_start,
            patch.object(workshop.subprocess, "Popen") as spawn,
        ):
            self.act(
                "alex",
                f"read {self.note} :3; do rewrite {self.note} "
                f"text={charter.q('- Newly edited rule waits for fresh memory.')}",
            )
            charter.sync(self.w, self.act, path, state)
            routing.record_knocks(self.w, corners)
            self.assertFalse(routing.news(self.w, resident, "pike", resting=True))
            subject = self.w.subjects[self.w.nodes[self.card]["subject"]]
            self.assertEqual(
                [], workshop.Workshop.heard(None, self.w, self.card, subject, wk, peek=True)
            )
            # Workers inherit Resident.send; that spy covers both kinds of turn.
            for method in (resident_start, resident_send, worker_start, spawn):
                method.assert_not_called()
        body = self.w.subjects[self.w.nodes[carried]["subject"]]["text"]
        self.assertIn("Newly edited rule", path.read_text(encoding="utf-8"))
        self.assertIn("Newly edited rule", body)
        self.assertFalse(any(e["verb"] == "knock" for e in self.w.events[start:]))
        self.assertFalse(any("charter read (" in line for _, line in self.calls))
        self.assertFalse(resident.state.get("calls"))
        self.assertFalse(resident.state.get("knocked_by"))
        self.assertEqual(old_worker, wk.state["charter_text"])
        self.assertEqual(old_resident, resident.state["charter_text"])
        # Reading the changed rules is deferred until a fresh start or compaction.
        _, cmd = self.start_worker()
        self.assertNotIn("Newly edited rule", cmd[cmd.index("--append-system-prompt") + 1])
        self.assertIn(
            "Newly edited rule",
            charter.collect(self.w, self.act, self.corner, "pike", "compaction"),
        )
        wk.state.pop("session")
        wk.save()
        _, cmd = self.start_worker()
        self.assertIn("Newly edited rule", cmd[cmd.index("--append-system-prompt") + 1])

    def test_oversize_warning_once_and_empty_source_clears_mirror(self):
        self.edit("\n".join(f"- Rule {i}: " + ("detail " * 40) for i in range(30)))
        path = self.tree / "AGENTS.md"
        state = {}
        charter.sync(self.w, self.act, path, state)
        warnings = [line for _, line in self.calls if "@jeff:" in line]
        self.assertEqual(1, len(warnings))
        charter.sync(self.w, self.act, path, state)
        self.assertEqual(1, sum("@jeff:" in line for _, line in self.calls))
        self.edit("")
        charter.sync(self.w, self.act, path, state)
        self.assertIn("charter: not read: note empty", path.read_text(encoding="utf-8"))
        self.assertNotIn("detail", path.read_text(encoding="utf-8"))

    def test_codex_resident_gets_charter_file_on_start(self):
        self.w.nodes[self.corner]["props"]["provider"] = "codex"
        r = house.Resident(self.h, self.corner)
        with (
            patch.object(house.subprocess, "Popen", return_value=MagicMock(pid=502)) as popen,
            patch.object(house.threading, "Thread"),
        ):
            r.start("test-model")
        cmd = popen.call_args.args[0]
        popen.call_args.kwargs["stderr"].close()
        path = Path(cmd[cmd.index("--charter-file") + 1])
        self.assertIn("Keep the sandbox", path.read_text(encoding="utf-8"))
        self.assertEqual("codex", r.state["session_provider"])

    def test_codex_reinjection_failure_is_reported(self):
        client = MagicMock()
        client.request.side_effect = RuntimeError("test refusal")
        args = SimpleNamespace(world="roomworld", target=self.card, actor="worker")
        output = []
        with (
            patch.object(charter, "live_reading", return_value=charter.read(self.w)),
            patch.object(charter, "report"),
        ):
            codex_resident.refresh_charter(client, "t1", args, output.append)
        self.assertEqual("charter_unavailable", output[-1]["subtype"])


if __name__ == "__main__":
    unittest.main()
