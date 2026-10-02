"""Prepare the per-commission worker provider hook; apply only with house stopped."""
# ruff: noqa: E501 -- exact source anchors for the existing workshop.

import argparse
import difflib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / "text-desk-lab/notation/workshop.py"
OLD = '''                cmd = [self.house.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                       "--model", model, "--permission-mode", "acceptEdits", "--allowedTools", *tools,
                       "--mcp-config", str(mcp), "--strict-mcp-config", "--setting-sources", "",
                       "--append-system-prompt", prompt]
'''
NEW = '''                current = self.house.load()
                task = s or current.subjects.get((current.nodes.get(self.cid) or {}).get("subject"), {})
                props = task.get("props") or {}
                provider = props.get("worker_provider", "claude")
                model = props.get("worker_model") or model
                bound = self.state.get("session_provider", "claude" if self.state.get("session") else provider)
                if bound != provider:
                    raise ValueError(f"{self.cid}: saved worker conversation belongs to {bound}, not {provider}; preserved")
                if provider == "codex":
                    adapter = HERE.parents[1] / "codex-residents" / "codex_worker.py"
                    instructions = self.dir / "worker-prompt.txt"
                    instructions.write_text(prompt + "\\n\\nCodex transport: use your native command, patch, image and web tools for the corresponding work above. The desk MCP tool is the same shared desk. Ask the commissioner there when stuck; no other agents or chats are exposed.\\n", encoding="utf-8")
                    cmd = [str(PY), str(adapter), "--model", model,
                           "--reasoning", props.get("worker_reasoning", "medium"),
                           "--prompt-file", str(instructions), "--mcp-config", str(mcp)]
                elif provider == "claude":
                    cmd = [self.house.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                           "--model", model, "--permission-mode", "acceptEdits", "--allowedTools", *tools,
                           "--mcp-config", str(mcp), "--strict-mcp-config", "--setting-sources", "",
                           "--append-system-prompt", prompt]
                else:
                    raise ValueError(f"{self.cid}: unknown worker provider {provider}")
                self.state["session_provider"] = provider
                self.state["model"] = model
                self.save()
'''


def candidate(source):
    if NEW in source:
        return source
    if source.count(OLD) != 1:
        raise ValueError("Workshop changed: review the provider hook against current source")
    result = source.replace(OLD, NEW)
    compile(result, str(TARGET), "exec")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = TARGET.read_text(encoding="utf-8")
    result = candidate(source)
    diff = "".join(difflib.unified_diff(
        source.splitlines(True), result.splitlines(True),
        fromfile="a/research/text-desk-lab/notation/workshop.py",
        tofile="b/research/text-desk-lab/notation/workshop.py",
    ))
    (HERE / "workshop-codex.patch").write_text(diff, encoding="utf-8")
    if args.apply:
        TARGET.write_text(result, encoding="utf-8")
        print("Applied per-commission worker provider hook")
    else:
        print(diff or "Hook already present")


if __name__ == "__main__":
    main()
