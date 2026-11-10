"""a7772 diagnosis only: actual CLI/store/charter code, disposable synthetic data.

No live session, service, model, host process or environment setting is touched.
The foreign writer identity and subprocess boundary are stand-ins.
"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import uuid
from unittest.mock import patch

import charter
import desk_mcp
import explore
import export_docs
import log_world
import roomworld
import store


def run():
    root = Path(__file__).resolve().parents[3] / ".agora-tmp" / "receipt-diagnosis" / uuid.uuid4().hex
    os.makedirs(root)
    path = root / "copy.pickle"
    owner, room = roomworld.build()
    w = owner.world
    w.apply("create", w.root, None, dict(kind="note", title=charter.DEFAULT_TITLE,
                                        role="agent-charter", text="- Keep tests off the real screen."), "jeff")
    target = room.CARDS[0]
    sid = w.nodes[target]["subject"]
    store.genesis(owner, path)
    with patch.object(explore, "holder_of", return_value=None):
        explore.save_desk(path, owner)
    original_file = path.read_bytes()
    before_comments = copy.deepcopy(w.subjects[sid]["comments"])
    receipts = []
    attempted_save = []
    real_save = explore.save_desk

    def blocked_save(file_path, local, data=None):
        attempted_save.append(copy.deepcopy(local.world.subjects[sid]["comments"]))
        return real_save(file_path, local, data)

    def cli_process(cmd, **kw):
        # The MCP wrapper is real, but its process is driven in this interpreter
        # with every session path redirected to our disposable fixture.
        assert Path(cmd[1]).name == "explore.py" and cmd[2] == "copy"
        assert kw["env"]["DESKD"] == "off"
        out = io.StringIO()
        error, code = "", 0
        try:
            with patch.object(explore, "SESSIONS", root), \
                    patch.object(sys, "argv", cmd[1:]), \
                    patch.object(sys, "stdin", io.StringIO(kw["input"])), \
                    patch.object(explore, "holder_of", return_value=os.getpid() + 100000), \
                    patch.object(explore, "save_desk", side_effect=blocked_save), \
                    patch.object(explore, "away_in", return_value=None), \
                    contextlib.redirect_stdout(out):
                explore.main()
        except RuntimeError as exc:
            code, error = 1, f"RuntimeError: {exc}"
        finally:
            explore.release_lock(root / "copy.lock")
        result = subprocess.CompletedProcess(cmd, code, out.getvalue(), error)
        receipts.append(result)
        return result

    try:
        # Same live() -> report() -> run_desk() -> explore path as compaction.
        # No HTTP request can run because DESKD is off.
        with patch.dict(os.environ, {"DESKD": "off"}), \
                patch.object(export_docs, "load", return_value=owner), \
                patch.object(desk_mcp.subprocess, "run", side_effect=cli_process):
            text = charter.live("copy", target, "worker-copy", "compaction")
        assert "standing rules" in text
        assert len(receipts) == 1 and receipts[0].returncode == 1
        assert "held by its world server" in receipts[0].stderr
        assert path.read_bytes() == original_file
        assert w.subjects[sid]["comments"] == before_comments
        assert len(attempted_save[0]) == len(before_comments) + 1
        added = attempted_save[0][-1]
        cid = added["id"]
        records = list(store.Log(store.log_path(path)).records())
        leaked = records[-1][0]
        leaked_fact = next(v for t, a, v in store.facts_of(leaked)
                           if t == sid and a == f"comment:{cid}")
        assert leaked_fact["text"] == added["text"]
        assert leaked["by"] == "house"
        leaked_event = next(p["e"] for p in leaked["parts"] if p.get("verb") == "comment")
        # Ordinary read-only loading already catches up records to the detached
        # file image, even though the active owner never accepted this comment.
        read_copy = explore.load_desk(path)
        assert any(c["id"] == cid for c in read_copy.world.subjects[sid]["comments"])
        assert path.read_bytes() == original_file

        replay = log_world.Replay()
        for rec, _ in records:
            replay.consume(rec, historical=True)
        # The actual active writer begins its next normal command with its own
        # unchanged in-memory world. begin() reconciles LOG to that world.
        ctx = store.safe_begin(owner, path)
        owner.repl(f"look {target} :1")
        owner.repl(f'do prop {target} diagnostic="normal owner command"')
        store.safe_commit(ctx, owner, "ordinary owner prop", "jeff")
        after = list(store.Log(store.log_path(path)).records())
        repair = after[len(records)][0]
        assert repair["parts"][0]["cause"] == "outside"
        removed = next(v for t, a, v in store.facts_of(repair)
                       if t == sid and a == f"comment:{cid}")
        assert removed is store.ABSENT
        for rec, _ in after[len(records):]:
            replay.consume(rec)
        assert any(d["aspect"] == f"comment:{cid}" and
                   d["reason"] == "unlogged edit repaired by logger" for d in replay.divergences)
        assert store.flatten(replay.world) == store.flatten(w)
        assert w.subjects[sid]["comments"] == before_comments
        assert path.read_bytes() == original_file
        latest = explore.load_desk(path)
        assert not any(c["id"] == cid for c in latest.world.subjects[sid]["comments"])
        actual_event = w.events[-1]["id"]
        assert leaked_event == actual_event
        return dict(
            synthetic=True, fixture="disposable; no live session",
            charter_context_returned_despite_failed_receipt=True,
            subprocess_returncode=receipts[0].returncode,
            save_refusal="held by its world server; send the line through the door",
            temporary_desk_held_comment=True, active_owner_held_comment=False,
            snapshot_unchanged=True, leaked_record=leaked["seq"],
            ghost_comment=cid, ghost_event=leaked_event,
            owner_event_reuses_ghost_id=actual_event,
            read_only_catch_up_temporarily_shows_ghost=True,
            repair_record=repair["seq"], repair_deleted_comment_from="log, not active owner",
            final_log_matches_owner=True, divergence_retained=True,
            final_read_only_catch_up_comment_absent=True,
        )
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(run(), indent=2))
