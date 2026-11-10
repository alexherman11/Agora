"""A replaced model process must not end its successor (JEFF, 28 Oct to 2 Nov 2026).

At a quota switch the house stopped JEFF's Claude process and started Codex; the Claude process's exit arrived a moment
later and cleared the new child, so Codex ran on unseen, held the conversation, and every later start was refused with
"thread ... already has an active writer". These tests run hidden: no window, no model.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import house as H                                   # noqa: E402
import transport as T                               # noqa: E402


class FakeHouse:
    def __init__(self, home):
        self.home = home

    def publish(self):
        pass


class Alive:
    def alive(self):
        return True


def make_agent(tmp_path):
    a = H.Agent(FakeHouse(tmp_path), {"name": "Jeff", "person": "p1"})
    return a


def test_a_replaced_process_exit_leaves_the_new_one(tmp_path):
    a = make_agent(tmp_path)
    old, new = Alive(), Alive()
    a.child = new
    a._event({"e": "exit", "code": 1, "child": old})
    assert a.child is new
    assert "error" not in a.state


def test_a_replaced_process_init_does_not_take_the_session(tmp_path):
    a = make_agent(tmp_path)
    old, new = Alive(), Alive()
    a.child, a.state["session"] = new, "new-thread"
    a._event({"e": "init", "session": "old-thread", "child": old})
    assert a.state["session"] == "new-thread"


def test_the_current_process_exit_still_counts(tmp_path):
    a = make_agent(tmp_path)
    cur = Alive()
    a.child = cur
    a._event({"e": "exit", "code": 1, "child": cur})
    assert a.child is None
    assert a.state["error"] == "its process ended (1)"


def test_kill_tree_ends_the_real_interpreter_behind_a_launcher(tmp_path):
    pidfile = tmp_path / "pid"
    code = f"import os,time; open(r'{pidfile}','w').write(str(os.getpid())); time.sleep(60)"
    proc = subprocess.Popen([sys.executable, "-c", code], creationflags=T.NO_WINDOW)
    for _ in range(100):
        if pidfile.exists() and pidfile.read_text():
            break
        time.sleep(0.1)
    real = int(pidfile.read_text())
    T.kill_tree(proc)
    proc.wait(timeout=10)
    time.sleep(0.5)
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {real}", "/NH"], capture_output=True, text=True).stdout
        assert str(real) not in out


class FakeMod:
    def __init__(self, rows):
        self.rows = rows

    def see(self, line):
        if line == 'look "Agent Book"':
            return {"rows": [{"text": (H.HERE / "fixtures/agent-book.md").read_text(encoding="utf-8")}]}
        t = line.split()[-1]
        return {"rows": [self.rows[t]] if t in self.rows else []}


def test_a_line_about_an_ask_says_where_it_was_asked():
    h = H.House.__new__(H.House)
    h.m = FakeMod({"dk9": {"kind": "ask-request", "where": "Why the agents stall · Writing", "about": "dk7"}})
    h.chat_name = lambda c: "Conversation"
    text = h.line_text("dk10", {"by_name": "Alex", "text": "edit in place", "about": "dk9"}, "dk1")
    assert text.endswith("edit in place [about: ask-request dk9, asked at Why the agents stall · Writing, on dk7]")
    plain = h.line_text("dk11", {"by_name": "Alex", "text": "yo"}, "dk1")
    assert plain.endswith(": yo")
