"""Check local inline Markdown links in the repository's current documentation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
FENCE = re.compile(r"^\s*(\x60{3,}|~{3,})")


def main() -> int:
    documents = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")])
    failures: list[str] = []
    checked = 0
    for document in documents:
        fence: str | None = None
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            marker = FENCE.match(line)
            if marker:
                if fence is None:
                    fence = marker[1][0]
                elif marker[1][0] == fence:
                    fence = None
                continue
            if fence is not None:
                continue
            for match in LINK.finditer(line):
                target = match[1].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                checked += 1
                destination = (document.parent / unquote(parsed.path)).resolve()
                if not destination.exists():
                    failures.append(f"{document.relative_to(ROOT)}:{line_number}: missing {target}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Checked {checked} local link targets in {len(documents)} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
