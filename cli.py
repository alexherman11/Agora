"""agora: the object layer at a terminal, without JEFF; also the debugger.
Never: never mutates except through verbs; never invents a view the kernel did not project."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Any

from kernel import events, project, scene, store, verbs
from kernel.schema import DESK
from kernel.text import Locator, TextDoc
from kernel.verbs import VerbError

DEFAULT_WORLD = os.environ.get("AGORA_WORLD", os.path.join("worlds", "default"))


def main(argv: Sequence[str] | None = None) -> int:
    return run(list(sys.argv[1:] if argv is None else argv), sys.stdout, sys.stderr)


def run(argv: list[str], out: IO[str], err: IO[str]) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(out)
        return 0
    try:
        world = verbs.open_world(args.world)
    except (events.LogError, OSError) as exc:
        print(f"cannot open world: {exc}", file=err)
        return 2
    if getattr(args, "viewer", None) is None:
        args.viewer = args.actor  # you see the world as yourself unless you ask otherwise
    try:
        return _COMMANDS[args.command](world, args, out)
    except VerbError as exc:
        print(f"refused: {exc}", file=err)
        return 2
    except (ValueError, TypeError, events.LogError, OSError) as exc:
        print(f"error: {exc}", file=err)
        return 2
    finally:
        world.close()


# -- commands -------------------------------------------------------------------------


def _init(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    verbs.ensure_desk(world, args.actor)
    print(f"world {world.world.path} ready; desk {DESK}", file=out)
    return 0


def _mint(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    facets = {facet_type: _json(body) for facet_type, body in args.facet or []}
    _selected_imports(world, facets.values())
    print(verbs.mint(world, args.actor, facets), file=out)
    return 0


def _attach(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    body = _json(args.body)
    _selected_imports(world, [body])
    record = verbs.attach(world, args.actor, args.entity, args.type, body)
    print(f"{record.entity} {record.type} r{record.revision}", file=out)
    return 0


def _read(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    print(json.dumps(verbs.read(world, args.actor, args.entity, args.type), indent=2), file=out)
    return 0


def _call(world, args, out):
    """Access the same registry as JEFF, including lens operations and retained reads."""
    fn = verbs.VERBS.get(args.verb)
    if fn is None:
        raise VerbError(f"unknown verb; choose from {sorted(verbs.VERBS)}")
    body = _json(args.arguments)
    if not isinstance(body, dict):
        raise VerbError("arguments must be a JSON object")
    if args.verb == "mint" and isinstance(body.get("facets"), dict):
        _selected_imports(world, body["facets"].values())
    elif args.verb == "attach":
        _selected_imports(world, [body.get("body")])
    result = fn(world, args.actor, **body)
    import dataclasses

    print(
        json.dumps(
            dataclasses.asdict(result) if dataclasses.is_dataclass(result) else result,
            ensure_ascii=False,
        ),
        file=out,
    )
    return 0


def _selected_imports(world, bodies):
    """A path explicitly supplied at the trusted terminal authorizes that exact file."""
    world.import_roots += tuple(
        Path(b["path"]).expanduser().resolve()
        for b in bodies
        if isinstance(b, dict) and isinstance(b.get("path"), str)
    )


def _place(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    transform = {
        k: v for k, v in (("x", args.x), ("y", args.y), ("scale", args.scale)) if v is not None
    }
    placed = verbs.place(world, args.actor, args.entity, args.mode, transform, args.scene)
    print(f"{placed.entity} on {args.scene} as {placed.mode} at {placed.transform}", file=out)
    return 0


def _log(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    for event in events.replay(world.world, after=args.after):
        if args.json:
            print(event.to_line(), file=out)
            continue
        when = time.strftime("%H:%M:%S", time.localtime(event.ts))
        print(
            f"{event.seq:>5}  {when}  {event.actor:<8} {event.kind:<18} {_summary(event)}", file=out
        )
    return 0


def _project(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    print(project.project(world, args.entity, args.viewer, args.budget), file=out)
    return 0


def _desk(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    print(project.project(world, DESK, args.viewer, args.budget), file=out)
    return 0


def _tree(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    print(json.dumps(scene.tree(world, args.viewer), indent=2), file=out)
    return 0


def _rebuild(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    fresh = store.rebuild(world.world)
    same = fresh.snapshot() == world.snapshot()
    print("identical" if same else "DIVERGED: the store no longer derives from the log", file=out)
    fresh.close()
    if args.write:
        world.close()
        store.rebuild(world.world, world.world.db).close()
        print(f"rewrote {world.world.db} from the log", file=out)
    return 0 if same else 1


def _edit(world: store.Store, args: argparse.Namespace, out: IO[str]) -> int:
    doc = TextDoc(world, args.actor, args.entity)
    if args.insert is not None:
        pos, text = args.insert
        doc.insert(int(pos), text)
    if args.delete is not None:
        pos, length = args.delete
        doc.delete(int(pos), int(length))
    if args.anchor is not None:
        start, end = args.anchor
        print(json.dumps(doc.anchor(int(start), int(end)).to_dict()), file=out)
    if args.resolve is not None:
        found = doc.resolve(Locator.from_dict(_json(args.resolve)))
        print(json.dumps(found.__dict__), file=out)
    record = doc.close()
    if record is not None:
        print(f"{record.entity} core.text r{record.revision}: {doc.plaintext()!r}", file=out)
    return 0


_COMMANDS = {
    "call": _call,
    "init": _init,
    "mint": _mint,
    "attach": _attach,
    "read": _read,
    "place": _place,
    "log": _log,
    "project": _project,
    "desk": _desk,
    "tree": _tree,
    "rebuild": _rebuild,
    "edit": _edit,
}


# -- parsing --------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agora", description="the object layer, at a terminal")
    parser.add_argument("--world", default=DEFAULT_WORLD, help="world directory")
    parser.add_argument(
        "--actor", default=os.environ.get("AGORA_ACTOR", getpass.getuser()), help="who is acting"
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="create the world and its desk")
    call = sub.add_parser(
        "call", help="call any registered verb, including preview_lens and activate_lens"
    )
    call.add_argument("verb")
    call.add_argument("arguments", help="JSON argument object")
    mint = sub.add_parser("mint", help="bring a new entity into the world")
    mint.add_argument("--facet", nargs=2, action="append", metavar=("TYPE", "JSON"))
    attach = sub.add_parser("attach", help="attach or update a facet")
    attach.add_argument("entity")
    attach.add_argument("type")
    attach.add_argument("body", help="the facet body as JSON")
    read = sub.add_parser("read", help="read facets at full fidelity")
    read.add_argument("entity")
    read.add_argument("type", nargs="?")
    place = sub.add_parser("place", help="place an entity on the desk")
    place.add_argument("entity")
    place.add_argument("--mode", default="icon", choices=["icon", "summary", "full"])
    place.add_argument("--x", type=float)
    place.add_argument("--y", type=float)
    place.add_argument("--scale", type=float)
    place.add_argument("--scene", default=DESK)
    log = sub.add_parser("log", help="every event, in order")
    log.add_argument("--after", type=int, default=0)
    log.add_argument("--json", action="store_true")
    proj = sub.add_parser("project", help="an entity at a token budget")
    proj.add_argument("entity")
    proj.add_argument("--budget", type=int, default=60)
    proj.add_argument("--viewer", default=None)
    desk = sub.add_parser("desk", help="the desk at a token budget")
    desk.add_argument("--budget", type=int, default=250)
    desk.add_argument("--viewer", default=None)
    tree = sub.add_parser("tree", help="the desk as the shell sees it")
    tree.add_argument("--viewer", default=None)
    rebuild = sub.add_parser("rebuild", help="derive a fresh store from the log and compare")
    rebuild.add_argument("--write", action="store_true", help="replace store.db with the rebuild")
    edit = sub.add_parser("edit", help="edit a core.text through the CRDT")
    edit.add_argument("entity")
    edit.add_argument("--insert", nargs=2, metavar=("POS", "TEXT"))
    edit.add_argument("--delete", nargs=2, metavar=("POS", "LEN"))
    edit.add_argument("--anchor", nargs=2, metavar=("START", "END"))
    edit.add_argument("--resolve", metavar="LOCATOR_JSON")
    return parser


def _json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"not JSON: {text!r} ({exc.msg})") from exc


def _summary(event: events.Event) -> str:
    p = event.payload
    match event.kind:
        case "entity-minted":
            return f"{p['entity']} with {sorted(p.get('facets', {})) or 'no facets'}"
        case "facet-attached" | "text-edited":
            body = p["body"]
            gist = body.get("name") or body.get("path") or body.get("text", "")
            return f"{p['entity']} {p['type']} {str(gist)[:40]!r}"
        case "appearance-placed":
            return f"{p['entity']} on {p['scene']} as {p['mode']}"
    return ""


if __name__ == "__main__":
    sys.exit(main())
