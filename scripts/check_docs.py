"""Validate Markdown/wiki links, heading targets and JSON examples in the design vault."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
WIKI = re.compile(r"\[\[([^\]\n]+)\]\]")
FENCE = re.compile(r"^\s*(\x60{3,}|~{3,})(.*)$")
INLINE = re.compile(r"\[\[[^\]\n]+\]\]|(\x60+).*?\1")


def slug(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"[^\w\s-]", "", text.lower()).replace(" ", "-")


def prose(document: Path, failures: list[str]) -> list[tuple[int, str]]:
    """Keep prose with source locations; validate rather than interpret examples."""
    lines: list[tuple[int, str]] = []
    fence: tuple[str, int, str, int] | None = None
    body: list[str] = []
    for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
        marker = FENCE.match(line)
        if fence is not None:
            if (
                marker
                and marker[1][0] == fence[0]
                and len(marker[1]) >= fence[1]
                and not marker[2].strip()
            ):
                if fence[2] == "json":
                    try:
                        json.loads("\n".join(body))
                    except json.JSONDecodeError as error:
                        failures.append(f"{document}:{fence[3]}: invalid JSON example: {error}")
                fence = None
                body = []
            else:
                body.append(line)
            continue
        if marker:
            fence = (marker[1][0], len(marker[1]), marker[2].strip(), number)
            continue
        lines.append((number, line))
    if fence is not None:
        failures.append(f"{document}:{fence[3]}: unclosed code fence")
    return lines


def main() -> int:
    documents = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")])
    failures: list[str] = []
    names: dict[str, list[Path]] = defaultdict(list)
    sources = {document.resolve(): prose(document, failures) for document in documents}
    anchors: dict[Path, set[str]] = {}
    for document, lines in sources.items():
        names[document.stem.casefold()].append(document)
        counts: dict[str, int] = defaultdict(int)
        headings: set[str] = set()
        for _, line in lines:
            match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
            if match:
                base = slug(match[1])
                occurrence = counts[base]
                headings.add(f"{base}-{occurrence}" if occurrence else base)
                counts[base] += 1
        anchors[document] = headings
    for name, matches in names.items():
        if len(matches) > 1:
            failures.append(f"Ambiguous wiki name {name}: {matches}")

    checked = 0
    for document, lines in sources.items():
        for number, line in lines:
            # Inline code can contain example link syntax that is not a real link.
            line = INLINE.sub(lambda match: match[0] if match[0].startswith("[[") else "", line)
            targets: list[tuple[Path | None, str, str, bool]] = []
            for match in LINK.finditer(line):
                target = match[1].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc:
                    continue
                destination = (document.parent / unquote(parsed.path)).resolve()
                if not parsed.path:
                    destination = document
                targets.append((destination, unquote(parsed.fragment), target, False))
            for match in WIKI.finditer(line):
                target = match[1].split("|", 1)[0]
                note, _, fragment = target.partition("#")
                matches = names.get(note.removesuffix(".md").casefold(), []) if note else [document]
                destination = matches[0] if len(matches) == 1 else None
                targets.append((destination, fragment, target, True))
            for destination, fragment, target, wiki in targets:
                checked += 1
                location = f"{document.relative_to(ROOT)}:{number}"
                if destination is None or not destination.exists():
                    failures.append(f"{location}: missing or ambiguous target {target}")
                elif fragment:
                    expected = slug(fragment) if wiki else fragment
                    if expected not in anchors.get(destination, set()):
                        failures.append(f"{location}: missing heading {target}")
    if failures:
        print("\n".join(failures))
        return 1
    print(
        f"Checked {checked} local links and heading targets in {len(documents)} Markdown files; "
        "JSON examples and code fences are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
