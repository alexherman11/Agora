"""Prepare/review the small house transport hook; --apply requires a deployment window."""
# ruff: noqa: E501 -- verbatim source anchors for the existing house.

import argparse
import difflib
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOUSE = HERE.parent / "text-desk" / "notation" / "house.py"
OLD = """        claude = self.house.claude
        cmd = [claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
               "--system-prompt", "", "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--model", model]
"""
NEW = """        props = (self.house.load().nodes.get(self.rid) or {}).get("props") or {}
        provider = props.get("provider", "claude")
        bound = self.state.get("session_provider", "claude" if self.state.get("session") else provider)
        if bound != provider:
            raise ValueError(f"{self.rid}: saved conversation belongs to {bound}, not {provider}; preserved")
        if provider == "codex":
            adapter = HERE.parents[1] / "codex" / "codex_resident.py"
            cmd = [sys.executable, str(adapter), "--model", model,
                   "--reasoning", props.get("reasoning", "medium")]
        elif provider == "claude":
            cmd = [self.house.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                   "--system-prompt", "", "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--model", model]
        else:
            raise ValueError(f"{self.rid}: unknown resident provider {provider}")
        self.state["session_provider"] = provider
"""


def candidate(source):
    if NEW in source:
        return source
    if source.count(OLD) != 1:
        raise ValueError("The house changed: review the transport hook against current source")
    result = source.replace(OLD, NEW)
    compile(result, str(HOUSE), "exec")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = HOUSE.read_text(encoding="utf-8")
    result = candidate(source)
    diff = "".join(
        difflib.unified_diff(
            source.splitlines(True),
            result.splitlines(True),
            fromfile="a/src/text-desk/notation/house.py",
            tofile="b/src/text-desk/notation/house.py",
        )
    )
    (HERE / "house-codex.patch").write_text(diff, encoding="utf-8")
    if args.apply:
        HOUSE.write_text(result, encoding="utf-8")
        print("Applied the reviewed transport hook; the house must start on this source.")
    else:
        print(diff or "Hook already applied.")


if __name__ == "__main__":
    main()
