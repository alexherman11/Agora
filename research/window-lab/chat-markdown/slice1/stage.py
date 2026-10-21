"""Exact offline body-only passages. No network, live apply or world-file access."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHES = {
    "a5210": {"name": "jeff-chat", "old": '    body : text "$s.said"\n      marks\n      role words\n      media',
              "new": '    body : text "$s.said"\n      markdown\n      role words\n      media\n      on link do view $value'},
    "a5086": {"name": "conversation", "old": '  body : text "$said"\n    marks\n    role body\n    media',
              "new": '  body : text "$said"\n    markdown\n    role body\n    media\n    on link do view $value'},
}


def prepare(texts, reverse=False):
    result = dict(texts)
    for item, h in PATCHES.items():
        old, new = (h["new"], h["old"]) if reverse else (h["old"], h["new"])
        if result[item].count(old) != 1:
            raise ValueError(f"{h['name']}: exact body changed/ambiguous; re-read, do not replace whole lens")
        result[item] = result[item].replace(old, new, 1)
    return result


def readable():
    blocks = ["# Richer chat — body-only staged changes",
              "Draft for JEFF, 20 October. No active lenses changed. Source must land first.",
              "Read both live lenses; save their complete text and revisions before writing. "
              "Check both OLD passages occur exactly once before either edit. Preserve all other text. "
              "If drifted, stop and refresh these hunks. The existing view verb handles named links; "
              "opening a link must not attach chat context. No composer, recipient, Reply or context hunk.",
              "For each lens replace OLD with NEW using ordinary do replace after read. "
              "Reverse by replacing NEW with OLD, after checking both fresh passages. "
              "Do not use the older lens.desk as an unreviewed activation shortcut."]
    for h in PATCHES.values():
        blocks.extend([f"## {h['name']}", "OLD (no trailing newline):\n\n```text\n" + h["old"] + "\n```",
                       "NEW (no trailing newline):\n\n```text\n" + h["new"] + "\n```"])
    blocks.append("Acceptance remains gated on fresh guarded disposable-feed proof at 320/420/600px "
                  "and the full HUD, including selection/copy, keyboard links, media playback/Pop out, "
                  "draft/caret/explicit context through incoming updates, and original-place replies. "
                  "No live Conversation sends, Alex-screen input or restart.")
    return "\n\n".join(blocks) + "\n"


if __name__ == "__main__":
    print(readable())
