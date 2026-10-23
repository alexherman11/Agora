"""Apply only the preserved reviewed edits to the prepared, hash-bound checkout."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import stage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "research/text-desk-lab/notation/"
PREPARED = "98627ab4274c3bbd31a5f19af4da51065f266929"
MAIN = "09ef2530ec848cbbcf0afc5d0934737095c3cc69"
CHECKPOINT = "1fb14a68426824d3ebd0dbf98346ab3f48caab6b"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def edits(before, after):
    a, b = before.splitlines(True), after.splitlines(True)
    return [(a[i:j], b[k:l]) for tag, i, j, k, l in
            difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
            if tag != "equal"]


def main():
    assert git("rev-parse", "HEAD").decode().strip() == PREPARED
    assert git("rev-parse", "main").decode().strip() == MAIN, "main drift: stop"
    inventory = {}
    for path in git("ls-tree", "-r", "--name-only", CHECKPOINT,
                    "research/task-wakes").decode().splitlines():
        saved = git("show", CHECKPOINT + ":" + path)
        current = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert current == saved, path
        inventory[path] = sha(saved)
    assert inventory["research/task-wakes/candidate.patch"] == (
        "52c3eca60b213d52789a29196b2ec6e9456fc23cfe935cc417d8491bcc8564db")
    manifest = json.loads((HERE / "manifest.json").read_text())
    originals, outputs = stage.candidates()
    old_sources = {n: git("show", "25b7caa:" + PREFIX + n).decode()
                   for n in originals}

    class Source:
        def __init__(self, name):
            self.name = name
        def read_text(self, **kwargs):
            return old_sources[self.name]

    class OldLab:
        def __truediv__(self, name):
            return Source(name)

    lab = stage.LAB
    try:
        stage.LAB = OldLab()
        _, reviewed = stage.candidates()
    finally:
        stage.LAB = lab
    report = {"prepared": PREPARED, "main": MAIN, "inventory": inventory, "files": {}}
    chunks = []
    for name in originals:
        old, new = originals[name], outputs[name]
        assert sha(old_sources[name].encode()) == manifest[PREFIX + name]["base_sha256"]
        assert sha(reviewed[name].encode()) == manifest[PREFIX + name]["candidate_sha256"]
        assert edits(old_sources[name], reviewed[name]) == edits(old, new), name
        assert old.encode() == git("show", MAIN + ":" + PREFIX + name), name
        if name == "house.py":
            # No voice/send/recovery or sampler lifecycle changes.
            def methods(text):
                tree = ast.parse(text)
                return {node.name: ast.dump(node, include_attributes=False)
                        for cls in tree.body if isinstance(cls, ast.ClassDef)
                        for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            before, after = methods(old), methods(new)
            assert {k for k in before if before[k] != after[k]} == {"news"}
        report["files"][name] = {"base_sha256": sha(old.encode()),
                                "output_sha256": sha(new.encode()),
                                "edit_groups": len(edits(old, new))}
        chunks.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                      fromfile="a/" + PREFIX + name, tofile="b/" + PREFIX + name))
        # Preserve exact baseline separately for production-vs-legacy integration tests.
        (HERE / ("integration-base-" + name + ".txt")).write_bytes(old.encode())
    patch = "".join(chunks).encode()
    report["patch_sha256"] = sha(patch)
    (HERE / "integration.patch").write_bytes(patch)
    (HERE / "integration-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, output in outputs.items():
        (lab / name).write_bytes(output.encode())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
