"""Discovery, migration parity and independent branch additions; no browser."""
import ast
import asyncio
import builtins
import dis
import hashlib
import importlib
import inspect
import json
import os
import shutil
import stat
from pathlib import Path
import subprocess
import sys
import textwrap
import types
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import hud_playtest as runner
import agora_tmp
from playtest_steps import discover
from playtest_steps import _support

HERE = Path(__file__).resolve().parent
BASELINE = json.loads((HERE / "playtest_steps_baseline.json").read_text(encoding="utf-8"))


def digest(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


class StandIn:
    """Records runner registration; executes only its real initial-paint step."""
    def __init__(self):
        self.w = types.SimpleNamespace(js=AsyncMock(return_value={"ok": True, "ms": 17}))
        self.copy = types.SimpleNamespace()
        self.rows = []

    async def step(self, sid, description, fn, budget=(100, 300)):
        row = dict(name=sid, description=description, budget=list(budget), outcome="registered")
        if fn.__name__ == "no":
            try:
                await fn()
            except runner.Skip:
                row["outcome"] = "skip"
        elif sid == "open":
            row["result"] = await fn()
        self.rows.append(row)
        return row


class Migration(unittest.IsolatedAsyncioTestCase):
    async def test_before_after_runner_on_identical_standins(self):
        # Read the pre-extraction source, but compile only its two factories.
        # No old module startup, world loading, browser or live effect runs.
        def original(path, name, env):
            source = subprocess.check_output(
                ["git", "show", f"{BASELINE['reference']}:src/desktop/{path}"],
                cwd=HERE, stderr=subprocess.PIPE).decode("utf-8")
            node = next(n for n in ast.parse(source).body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
            exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), env)
            return env[name]
        old_walk = original("hud_playtest.py", "walk", dict(vars(runner)))
        import hud_scroll
        old_scroll = original("hud_scroll.py", "steps", dict(vars(hud_scroll)))
        for only in (None, ["scroll"], ["writing", "open"], ["workspace"], ["no-such-step"]):
            before, after = StandIn(), StandIn()
            with patch("hud_playtest.asyncio.sleep", new=AsyncMock()):
                with patch("hud_scroll.steps", old_scroll):
                    await old_walk(before, only)
                await runner.walk(after, only)
            old_names = {row["name"] for row in before.rows}
            self.assertEqual(before.rows, [row for row in after.rows if row["name"] in old_names], only)

    def test_original_registrations_and_budgets(self):
        steps = {s.name: s for s in discover()}
        for old in BASELINE["steps"]:
            step = steps[old["name"]]
            self.assertEqual(step.description, old["description"])
            self.assertEqual(step.order, old["order"])
            self.assertEqual(list(step.budget), old["budget"])
            self.assertEqual([list(n) for n in step.needs], old["needs"])

    def test_original_script_and_assertion_bodies_unchanged(self):
        for old in BASELINE["steps"]:
            tree = ast.parse((HERE / "playtest_steps" / (old["name"] + ".py")).read_text(encoding="utf-8"))
            bind = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "bind")
            if old["function"]:
                fn = next(n for n in bind.body if isinstance(n, ast.AsyncFunctionDef))
                self.assertEqual(digest(fn), old["body"], old["name"])
            else:
                self.assertEqual(ast.dump(bind.body[-1].value), old["body"], old["name"])
        tree = ast.parse(inspect.getsource(_support))
        for name, expected in BASELINE["helpers"].items():
            node = next(n for n in ast.walk(tree)
                        if (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
                        or (isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name))
            self.assertEqual(digest(node), expected, name)
        workspace = ast.parse((HERE / "playtest_steps/workspace.py").read_text(encoding="utf-8"))
        for name, expected in BASELINE["workspace_constants"].items():
            node = next(n for n in workspace.body if isinstance(n, ast.Assign) and n.targets[0].id == name)
            self.assertEqual(digest(node), expected, name)

    def test_all_callbacks_bind_and_resolve_their_globals(self):
        play = StandIn()
        def check(code, env):
            for instruction in dis.get_instructions(code):
                if instruction.opname == "LOAD_GLOBAL":
                    name = instruction.argval
                    self.assertTrue(name in env or hasattr(builtins, name), (code.co_name, name))
            for child in code.co_consts:
                if isinstance(child, types.CodeType):
                    check(child, env)
        for step in discover():
            callback = step.script(play, {"ok": True})
            self.assertTrue(callable(callback), step.name)
            check(callback.__code__, callback.__globals__)
        for helper in vars(_support.helpers(play)).values():
            check(helper.__code__, helper.__globals__)
        for helper in vars(_support.wheel_helpers(play)).values():
            if callable(helper):
                check(helper.__code__, helper.__globals__)

    async def test_complete_runner_registration_and_first_paint(self):
        play = StandIn()
        with patch("hud_playtest.asyncio.sleep", new=AsyncMock()):
            await runner.walk(play, None)
        self.assertEqual([r["name"] for r in play.rows], [s.name for s in discover()])
        self.assertEqual([r["budget"] for r in play.rows], [list(s.budget) for s in discover()])
        self.assertEqual(play.rows[0]["result"]["ms"], 17)
        play.w.js.assert_awaited_once()

    async def test_only_and_scroll_alias_keep_skipped_rows(self):
        play = StandIn()
        with patch("hud_playtest.asyncio.sleep", new=AsyncMock()):
            await runner.walk(play, ["scroll"])
        self.assertEqual([r["name"] for r in play.rows if r["outcome"] != "not played"],
                         [s.name for s in discover() if s.name.startswith("scroll")])
        self.assertEqual(len(play.rows), len(discover()))

    async def test_existing_writing_press_success_and_failed_assertion(self):
        step = next(s for s in discover() if s.name == "writing")
        play = StandIn()
        play.has = AsyncMock(return_value=True)
        play.timed = AsyncMock(return_value={"ok": True, "ms": 42})
        self.assertEqual(await step.script(play, None)(),
                         {"ok": True, "ms": 42, "note": "Writing opened inside the home base"})
        play.has.return_value = False
        with self.assertRaisesRegex(AssertionError, "no Writing room"):
            await step.script(play, None)()

    async def test_existing_dependency_skip(self):
        step = next(s for s in discover() if s.name == "scrollreader")
        play = StandIn()
        def needs(*args):
            raise runner.Skip("not landed")
        play.needs = needs
        with self.assertRaisesRegex(runner.Skip, "not landed"):
            await step.script(play, None)()
        play.w.js.assert_not_awaited()

    async def test_workspace_press_back_and_changed_panels_failure(self):
        step = next(s for s in discover() if s.name == "workspace")
        for after, okay in (("Chat|Viewer", True), ("Chat|Music|Viewer", False)):
            play = StandIn()
            play.w.js = AsyncMock(side_effect=["Chat|Viewer", True, after])
            play.needs = lambda *args: None
            play.has = AsyncMock(return_value=True)
            play.timed = AsyncMock(side_effect=[{"ok": True, "ms": 41}, {"ok": True, "ms": 43}])
            result = await step.script(play, None)()
            self.assertEqual(result["ok"], okay)
            self.assertEqual(play.timed.await_count, 2)
            if okay:
                self.assertIn("same panels out as before", result["note"])
            else:
                self.assertIn("back did not return the panels", result["want"])

    def test_wheel_factory_compatibility(self):
        from hud_scroll import steps
        expected = [s for s in discover() if s.name.startswith("scroll")]
        rows = steps(StandIn())
        self.assertEqual([(r[0], r[1], r[3]) for r in rows],
                         [(s.name, s.description, s.budget) for s in expected])


TEMPLATE = """from playtest_steps import Step
def bind(play, opened):
    async def check():
        return {{"note": {name!r}}}
    return check
STEP = Step(name={name!r}, description={name!r}, order={order},
            needs=(), script=bind, assertion="painted", budget=(100, 300))
"""


class Discovery(unittest.TestCase):
    def setUp(self):
        self.root = Path(agora_tmp.directory("step-test-")).resolve()
        self.package = "steps_" + uuid4().hex
        self.directory = self.root / self.package
        self.directory.mkdir()
        (self.directory / "__init__.py").write_text("", encoding="utf-8")
        sys.path.insert(0, str(self.root))

    def tearDown(self):
        sys.path.remove(str(self.root))
        for key in list(sys.modules):
            if key == self.package or key.startswith(self.package + "."):
                del sys.modules[key]
        self.assertTrue(self.root.is_relative_to(HERE.parents[1]))
        self.assertTrue(self.root.name.startswith("step-test-"))
        def remove_readonly(function, path, error):
            # Git's fixture objects have the Windows read-only attribute.
            target = Path(path).resolve()
            self.assertTrue(target.is_relative_to(self.root))
            target.chmod(stat.S_IWRITE | stat.S_IREAD)
            function(path)
        shutil.rmtree(self.root, onexc=remove_readonly)

    def add(self, file, name, order=100):
        (self.directory / (file + ".py")).write_text(TEMPLATE.format(name=name, order=order), encoding="utf-8")

    def test_scan_includes_new_files_and_orders_ties(self):
        self.add("z", "z", 100)
        self.add("a", "a", 100)
        self.add("first", "first", 10)
        (self.directory / "_helper.py").write_text("raise AssertionError('not a step')", encoding="utf-8")
        self.assertEqual([s.name for s in discover(self.directory, self.package)], ["first", "a", "z"])
        self.add("new", "new", 50)
        self.assertEqual([s.name for s in discover(self.directory, self.package)], ["first", "new", "a", "z"])

    def test_duplicate_names_fail_loudly(self):
        self.add("a", "same")
        self.add("b", "same")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            discover(self.directory, self.package)

    def test_missing_export_fails_loudly(self):
        (self.directory / "broken.py").write_text("STEP = None", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "export STEP"):
            discover(self.directory, self.package)

    def test_two_branch_additions_merge_without_checkout_or_shared_list(self):
        # Bare fixture object database only: no project index, ORIG_HEAD,
        # checkout, new project worktree or git merge operation.
        repo = self.root / "fixture.git"
        env = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@local",
                   GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@local")
        def git(*args, stdin=None):
            return subprocess.check_output(["git", "--git-dir", str(repo), *args],
                                           input=stdin, env=env, stderr=subprocess.PIPE).decode().strip()
        subprocess.run(["git", "init", "--bare", str(repo)], check=True, capture_output=True)
        def tree(files):
            entries = []
            for name, content in sorted(files.items()):
                if isinstance(content, dict):
                    entries.append(f"040000 tree {tree(content)}\t{name}\n")
                else:
                    blob = git("hash-object", "-w", "--stdin", stdin=content.encode())
                    entries.append(f"100644 blob {blob}\t{name}\n")
            return git("mktree", stdin="".join(entries).encode())
        def commit(files, parent=None):
            args = ["commit-tree", tree(files)]
            if parent:
                args.extend(["-p", parent])
            return git(*args, stdin=b"fixture\n")
        unchanged_runner = "scan playtest_steps; sort by order,name\n"
        base_files = {"hud_playtest.py": unchanged_runner, "playtest_steps": {"__init__.py": ""}}
        base = commit(base_files)
        left = commit({"hud_playtest.py": unchanged_runner, "playtest_steps":
                       {"__init__.py": "", "left.py": TEMPLATE.format(name="left", order=100)}}, base)
        right = commit({"hud_playtest.py": unchanged_runner, "playtest_steps":
                        {"__init__.py": "", "right.py": TEMPLATE.format(name="right", order=100)}}, base)
        merged = git("merge-tree", "--write-tree", left, right)
        self.assertNotIn("\n", merged, "merge-tree reported a conflict")
        files = git("ls-tree", "-r", "--name-only", merged).splitlines()
        self.assertEqual(files, ["hud_playtest.py", "playtest_steps/__init__.py",
                                 "playtest_steps/left.py", "playtest_steps/right.py"])
        self.assertEqual(git("show", f"{merged}:hud_playtest.py"), unchanged_runner.strip())
        for name in ("left", "right"):
            (self.directory / (name + ".py")).write_text(git("show", f"{merged}:playtest_steps/{name}.py"), encoding="utf-8")
        self.assertEqual([s.name for s in discover(self.directory, self.package)], ["left", "right"])


if __name__ == "__main__":
    unittest.main()
