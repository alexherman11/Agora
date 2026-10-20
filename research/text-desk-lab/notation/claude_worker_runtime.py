"""Claude worker options, passed to the runtime (never a second compaction loop).

Installed Claude Code 2.1.287 --help advertises medium effort and a numeric
100k–1M autocompact window. Unknown values fail instead of silently substituting.
No account/profile access is needed to build these arguments.
"""
import re


def arguments(cfg):
    effort = str(cfg.get("worker_claude_effort") or "medium")
    if effort not in ("low", "medium", "high", "xhigh", "max"):
        raise ValueError("unsupported Claude worker effort: " + effort)
    compact = str(cfg.get("worker_claude_autocompact") or "600k")
    match = re.fullmatch(r"(\d+)([kKmM]?)", compact)
    if not match:
        raise ValueError("Claude worker autocompact must be a token count")
    tokens = int(match[1]) * {"": 1, "k": 1000, "m": 1000000}[match[2].lower()]
    if not 100000 <= tokens <= 1000000:
        raise ValueError("Claude worker autocompact must be 100k–1M tokens")
    return ["--effort", effort, "--autocompact", compact]
