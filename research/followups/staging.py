"""Hash-checked integration payload. No apply/launch command; review only."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LAB = "research/text-desk-lab/notation/"
HUNKS = {
    LAB + "house.py": [
        ("import host_route_parent\n", "import host_route_parent\nimport followups\n"),
        ('COMMANDS = {"look",', 'COMMANDS = {"followups", "look",'),
        ('        self.charter_state = {}\n',
         '        self.charter_state = {}\n'
         '        self.followups = followups.HouseBridge(self.dir / "followups.json")\n'),
        ('        cfg = self.settings(w)\n',
         '        self.followups.observe(w)\n'
         '        cfg = self.settings(w)\n'),
        ('            if not r.state.get("woke"):\n',
         '            self.followups.dispatch(w, self.residents)\n'
         '            if r.busy:  # explicit follow-up sent; ordinary news remains unread for next turn\n'
         '                continue\n'
         '            if not r.state.get("woke"):\n'),
    ],
    LAB + "desk.py": [
        ('BASE_COMMANDS = {"help",', 'BASE_COMMANDS = {"followups", "help",'),
        ('        if cmd == "log-world":\n',
         '        if cmd == "followups":\n'
         '            import followups\n'
         '            return followups.command(self, argv)\n'
         '        if cmd == "log-world":\n'),
    ],
}


def texts():
    manifest = json.loads((HERE / "integration.json").read_text(encoding="utf-8"))
    out = {}
    for relative, hunks in HUNKS.items():
        path = ROOT / relative
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["bases"][relative]:
            raise ValueError("integration base changed: " + relative)
        text = raw.decode("utf-8").replace("\r\n", "\n")
        for old, new in hunks:
            if text.count(old) != 1:
                raise ValueError("integration hunk not unique: " + relative + " " + old[:80])
            text = text.replace(old, new)
        ast.parse(text, filename=relative)
        out[relative] = text
    return out


if __name__ == "__main__":
    # Only prints/checks. Never writes production source or starts a runtime.
    for name, text in texts().items():
        print(name, "staged", hashlib.sha256(text.encode()).hexdigest())
