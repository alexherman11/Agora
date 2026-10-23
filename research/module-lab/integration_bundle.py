"""Prepare new world objects for reviewed live integration; never load/save a session.

Prepared live commands use the mandatory source/runtime deployment gate below.
There is no automatic installation or service control. Fixture installation
remains deliberately restricted to a new in-memory desk.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research/text-desk-lab/notation"
sys.path.insert(0, str(LAB))

from module_examples import coverage_document, registry  # noqa: E402
from module_preview import LENS  # noqa: E402

BUNDLE = "crew-capabilities-2026-10-22"


def q(value):
    return (
        '"'
        + str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("\n", "\\n")
        + '"'
    )


def manifest():
    plan = coverage_document(registry(), frames=2)
    base = dict(
        plan=plan,
        input=dict(
            title="Example workshop time",
            unit="hours",
            intervals=[dict(start=0, end=5), dict(start=3, end=8)],
        ),
    )
    configs = {
        "KNOWN": base,
        "STALE": {**base, "state": "stale"},
        "MISSING": {**base, "source": "missing-calendar-producer", "into": "intervals"},
    }
    notes = []

    def note(key, title, text, tag="", **props):
        notes.append(dict(key=key, title=title, text=text, tag=tag, props=props))

    note(
        "terminal",
        "crew-terminal-style",
        (ROOT / "research/window-lab/data-dashboard/terminal.style").read_text(encoding="utf-8"),
        "style",
    )
    note(
        "module_style",
        "composition-workshop-style",
        (ROOT / "research/window-lab/data-dashboard/dashboard.style").read_text(encoding="utf-8"),
        "style",
    )
    for key, config in configs.items():
        note(key, "Composition example " + key.lower(), json.dumps(config))
    note(
        "crew",
        "crew-observatory",
        (HERE / "crew-live.lens").read_text(encoding="utf-8"),
        "lens",
        style="crew-terminal-style",
    )
    workshop = LENS.replace(
        "Read-only preview. No live world, model calls or action execution.",
        "Demonstration inputs. Module evaluation has no effects.",
    )
    workshop = workshop.replace(
        "result : column",
        """  crew : text "Open Crew observatory", role tool
    on click host window crew-observatory
  catalog : text "Inspect available capabilities", role tool
    on click host window composition-catalog
  trace : text "Inspect this composition", role tool
    on click host window composition-trace
result : column""",
    )
    note("workshop", "composition-workshop", workshop, "lens", style="composition-workshop-style")
    for key, title, source in (
        ("catalog", "composition-catalog", "modules"),
        ("trace", "composition-trace", "modules:@KNOWN@/trace"),
    ):
        note(
            key,
            title,
            f"""root : column, role dashboard
  title : text "Capabilities / inspected evidence", role hero
  rows : column
    of {source} as m
    each entry
entry : column, role card
  heading : text "$m.title", role section
  summary : text "$m.summary", role body
  evidence : column
    fold "Details"
    words : text "$m.detail", role meta
""",
            "lens",
            style="composition-workshop-style",
        )
    note(
        "guide",
        "Crew and capabilities",
        "Crew observatory reads existing publications without writing world telemetry. "
        "Composition workshop uses labelled synthetic examples, "
        "two capabilities and nested frames. "
        "No model calls, effect execution, migrations, or audience code. "
        "Workers opens inside the HUD viewer with Back; Modules opens its own window.",
    )
    return dict(
        bundle=BUNDLE,
        notes=notes,
        dock=[
            dict(title="Workers", glyph="▤", opens="@crew@"),
            dict(title="Modules", glyph="◇", window="composition-workshop"),
        ],
    )



def deploy_command(files, line, *, url, world, actor):
    """Replay one reviewed module/dashboard install command, without retries.

    The integration owner supplies the complete reviewed dependency closure.
    Both the client and answering backend require exact committed source; the
    backend additionally checks its loaded revision and startup byte inventory.
    Ordinary preview telemetry reads do not use this mutation boundary.
    """
    from deployment_preflight import deploy_line

    return deploy_line(ROOT, files, line, url=url, world=world, actor=actor)


def install_memory(desk, bundle=None):
    """Fixture-only normal commands, with a transcript for reviewing an installer."""
    if getattr(desk, "_session", "") != "crew-integration-memory":
        raise ValueError("fixture installation accepts only crew-integration-memory")
    bundle = bundle or manifest()
    existing = {s.get("title") for s in desk.world.subjects.values()}
    if existing & {n["title"] for n in bundle["notes"]}:
        raise ValueError("existing title collision; no overwrite")
    refs, commands = {}, []

    def run(line):
        commands.append(line)
        result = desk.dispatch("desk", dict(line=line, whole=True))
        text = result.get("text", "")
        if result.get("error") or text.startswith("ERR"):
            raise ValueError(result)
        made = re.search(r"created ([af]\d+)", text)
        return made[1] if made else None

    for note in bundle["notes"]:
        text = note["text"]
        for key, value in refs.items():
            text = text.replace("@" + key + "@", value)
        run("look " + desk.world.root)
        item = run(f"do create {desk.world.root} kind=note title={q(note['title'])} text={q(text)}")
        if item is None:
            raise ValueError("missing create receipt")
        refs[note["key"]] = item
        run("look " + item)
        props = {"integration_bundle": BUNDLE, "integration_key": note["key"], **note["props"]}
        run("do prop " + item + " " + " ".join(k + "=" + q(v) for k, v in props.items()))
        if note["tag"]:
            run(f"do tag {item} add={note['tag']}")
    return refs, commands


if __name__ == "__main__":
    print(json.dumps(manifest(), ensure_ascii=False, indent=2))
