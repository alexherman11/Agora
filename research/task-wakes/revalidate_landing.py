"""Verify exact reviewed source, rerun only offline imports; keep old evidence."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "research/text-desk-lab/notation/"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def methods(source):
    return {cls.name + "." + node.name: ast.dump(node, include_attributes=False)
            for cls in ast.parse(source).body if isinstance(cls, ast.ClassDef)
            for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    manifest = json.loads((HERE / "integration-manifest.json").read_text())
    assert git("rev-parse", "HEAD").decode().strip() == manifest["prepared"], "HEAD moved"
    assert git("rev-parse", "main").decode().strip() == manifest["main"], "main moved"
    assert sha((HERE / "integration.patch").read_bytes()) == manifest["patch_sha256"]
    files = {}
    for name, expected in manifest["files"].items():
        path = PREFIX + name
        source = (ROOT / path).read_bytes()
        base = git("show", manifest["main"] + ":" + path)
        assert sha(source) == expected["output_sha256"], name + ": output drift"
        assert sha(base) == expected["base_sha256"], name + ": base drift"
        assert (HERE / ("integration-base-" + name + ".txt")).read_bytes() == base
        files[path] = {"base_sha256": sha(base), "output_sha256": sha(source),
                       "edit_groups": expected["edit_groups"]}
        if name == "house.py":
            before, after = methods(base), methods(source)
            assert before.keys() == after.keys()
            assert [key for key in before if before[key] != after[key]] == ["House.news"]
    for path, expected in manifest["inventory"].items():
        assert sha((ROOT / path).read_bytes().replace(b"\r\n", b"\n")) == expected, path
    tracked = set(git("diff", "--name-only").decode().splitlines())
    assert tracked == {*files, ".gitignore"}, ("unexpected tracked scope", tracked)
    out = HERE / "landing-revalidation-final"
    out.mkdir(exist_ok=True)
    # Import reviewed runner only after hashes/scope pass. All runtime work is
    # fixtures; no House.run, provider, native launch or production session.
    import run_integration
    run_integration.OUTPUT = out  # retain original logs and baseline lookup paths
    run_integration.main()
    report = {"head": manifest["prepared"], "main": manifest["main"],
              "patch_sha256": manifest["patch_sha256"], "files": files,
              "production_edit_groups": sum(f["edit_groups"] for f in files.values()),
              "house_changed_methods": ["House.news"],
              "bookkeeping": {".gitignore": "root pytest-cache-files-* only"},
              "tests": json.loads((out / "integration-results.json").read_text()),
              "policy": "no enable act; absence independently read through Desk"}
    (out / "candidate.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Exact source/inventory/base verification passed; production edit groups:",
          report["production_edit_groups"])


if __name__ == "__main__":
    main()
