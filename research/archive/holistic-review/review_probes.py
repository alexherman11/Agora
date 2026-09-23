"""Review-only counterexamples, using disposable synthetic worlds and no model calls.

Run from the repository root: uv run python research/holistic-review/review_probes.py
This is evidence for a review, not a replacement for the project's regression suite.
Corruption is injected only into temporary fixture logs. Production files are untouched.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kernel import events, project, scene, store, verbs  # noqa: E402
from kernel.text import TextDoc  # noqa: E402


def run() -> dict:
    results = {}
    opened = []
    with tempfile.TemporaryDirectory(prefix="agora-review-") as scratch:
        base = Path(scratch).resolve()

        def world(name):
            location = (base / name).resolve()
            assert location.is_relative_to(base)
            value = verbs.open_world(location)
            opened.append(value)
            return value

        def attempt(fn):
            try:
                return {"value": fn()}
            except BaseException as exc:
                return {"error": type(exc).__name__, "detail": str(exc)[:250]}

        try:
            w = world("atomic")
            entity = verbs.mint(w, "alex")
            before = w.world.log.read_bytes()
            refused = attempt(lambda: verbs.place(w, "alex", entity, mode="invalid"))
            results["refused_place_on_uninitialized_desk"] = {
                **refused,
                "log_unchanged": w.world.log.read_bytes() == before,
                "events_added": len(list(events.replay(w.world))) - 1,
            }

            w = world("oversize")
            source = base / "large.txt"
            source.write_text("a" * 1_000_001, encoding="utf-8")
            entity = verbs.mint(w, "alex", {"core.text": {"path": str(source)}})
            results["path_import_bypasses_text_limit"] = {
                "configured_limit": 1_000_000,
                "accepted_characters": len(w.facet(entity, "core.text").body["text"]),
            }

            w = world("orphan")
            source = base / "artifact.txt"
            source.write_text("synthetic private fixture", encoding="utf-8")
            before = w.world.log.read_bytes()
            refused = attempt(
                lambda: verbs.mint(
                    w,
                    "alex",
                    {
                        "core.file-backing": {"path": str(source)},
                        "core.name": {"name": 123},
                    },
                )
            )
            results["refused_mint_retains_imported_blob"] = {
                **refused,
                "log_unchanged": w.world.log.read_bytes() == before,
                "blob_count": len(list(w.world.blobs.iterdir())),
            }

            w = world("cycle")
            desk = verbs.ensure_desk(w)
            verbs.place(w, "alex", desk)
            results["legal_scene_self_reference"] = {
                "projection": attempt(lambda: project.project(w, desk, "alex", 250)),
                "tree": attempt(lambda: scene.tree(w, "alex")),
            }

            w = world("anchor")
            entity = verbs.mint(w, "alex", {"core.text": {"text": "hello world"}})
            first = TextDoc(w, "alex", entity)
            locator = first.anchor(6, 11)
            first.close()
            second = TextDoc(w, "alex", entity)
            results["anchor_reopen_without_prior_edit"] = {
                "snapshot_persisted": "snapshot" in w.facet(entity, "core.text").body,
                "resolution": attempt(lambda: asdict(second.resolve(locator))),
            }

            w = world("two-editors")
            entity = verbs.mint(w, "alex", {"core.text": {"text": "hello"}})
            seed = TextDoc(w, "alex", entity)
            seed.insert(5, " world")
            seed.flush()
            editor_a = TextDoc(w, "alex", entity)
            editor_b = TextDoc(w, "jeff", entity)
            editor_a.insert(0, "A ")
            editor_b.insert(11, " B")
            editor_a.flush()
            editor_b.flush()
            results["two_text_editors"] = {
                "first_local": editor_a.plaintext(),
                "second_local": editor_b.plaintext(),
                "persisted": w.facet(entity, "core.text").body["text"],
                "both_edits_present": w.facet(entity, "core.text").body["text"]
                == "A hello world B",
                "rebuild_equals_store": store.rebuild(w.world).snapshot() == w.snapshot(),
            }

            w = world("rewrite-anchor")
            entity = verbs.mint(w, "alex", {"core.text": {"text": "hello world"}})
            first = TextDoc(w, "alex", entity)
            first.insert(0, "a ")
            first.flush()
            locator = first.anchor(8, 13)
            verbs.attach(w, "jeff", entity, "core.text", {"text": "replacement"})
            second = TextDoc(w, "alex", entity)
            results["anchor_after_plain_replacement"] = attempt(
                lambda: asdict(second.resolve(locator))
            )

            w = world("projection")
            entity = verbs.mint(
                w,
                "jeff",
                {
                    "core.name": {"name": "notes"},
                    "core.text": {"text": "word " * 100},
                    "core.file-backing": {"path": str(source)},
                },
            )
            selection = project.select(w, entity, "alex", "context", 12)
            rendered = project.render_tokens(selection)
            long_name = verbs.mint(w, "alex", {"core.name": {"name": "N" * 100}})
            results["projection_budget_and_label"] = {
                "budget": 12,
                "rendered": rendered,
                "rendered_estimated_tokens": project.tokens(rendered),
                "long_name_label": project.render_tokens(
                    project.select(w, long_name, "alex", "label", 12)
                ),
            }

            w = world("tail-scan")
            for _ in range(30):
                verbs.mint(w, "alex")
            w.sync()
            real_open = open
            reads = []

            class MeteredFile:
                def __init__(self, handle):
                    self.handle = handle

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return self.handle.__exit__(*args)

                def read(self, *args):
                    value = self.handle.read(*args)
                    reads.append(len(value))
                    return value

                def __getattr__(self, key):
                    return getattr(self.handle, key)

            def metered_open(path, mode="r", *args, **kwargs):
                handle = real_open(path, mode, *args, **kwargs)
                if Path(path) == w.world.log and mode == "r":
                    return MeteredFile(handle)
                return handle

            with patch("builtins.open", metered_open):
                w.sync()
                w.sync()
            results["no_op_sync_reads_entire_log"] = {
                "log_bytes": w.world.log.stat().st_size,
                "characters_read_per_sync": reads,
            }

            w = world("sync-interleaving")
            entity = verbs.mint(w, "alex", {"core.text": {"text": "one"}})
            barrier = threading.Barrier(2)
            first_done = threading.Event()
            real_replay = events.replay
            errors = []

            def scheduled_replay(target, after=0):
                pending = list(real_replay(target, after=after))
                barrier.wait(timeout=5)
                if threading.current_thread().name == "review-second":
                    assert first_done.wait(5)
                yield from pending

            def sync_worker():
                try:
                    w.sync()
                except BaseException as exc:
                    errors.append(type(exc).__name__ + ": " + str(exc))
                finally:
                    if threading.current_thread().name == "review-first":
                        first_done.set()

            with patch.object(events, "replay", scheduled_replay):
                threads = [
                    threading.Thread(target=sync_worker, name="review-" + name)
                    for name in ("first", "second")
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(10)
                assert not any(thread.is_alive() for thread in threads)
            rebuilt = store.rebuild(w.world)
            opened.append(rebuilt)
            results["concurrent_sync_duplicate_application"] = {
                "scheduling": (
                    "Both readers capture the same cursor; SQL applications then run serially."
                ),
                "errors": errors,
                "log_events": events.count(w.world),
                "cached_facet_revision": w.facet(entity, "core.text").revision,
                "rebuilt_facet_revision": rebuilt.facet(entity, "core.text").revision,
                "rebuild_equals_store": rebuilt.snapshot() == w.snapshot(),
            }

            w = world("corruption")
            entity = verbs.mint(w, "alex", {"core.text": {"text": "first"}})
            verbs.attach(w, "alex", entity, "core.text", {"text": "second"})
            verbs.attach(w, "alex", entity, "core.text", {"text": "third"})
            w.sync()
            # Deliberate corruption of a disposable fixture, never a real world.
            lines = w.world.log.read_bytes().splitlines(keepends=True)
            lines[1] = b"damaged complete middle line\n"
            w.world.log.write_bytes(b"".join(lines))
            rebuilt = store.rebuild(w.world)
            opened.append(rebuilt)
            results["middle_corruption_silently_skipped"] = {
                "rebuild_raised": False,
                "cached_revision": w.facet(entity, "core.text").revision,
                "rebuilt_revision": rebuilt.facet(entity, "core.text").revision,
                "rebuild_equals_store": rebuilt.snapshot() == w.snapshot(),
            }

            w = world("utf8-tail")
            verbs.mint(w, "alex")
            with w.world.log.open("ab") as handle:
                handle.write(b'{"incomplete":"\xe2')
            results["torn_multibyte_tail"] = attempt(lambda: events.count(w.world))

            w = world("file-authority")
            source = base / "backed.txt"
            source.write_text("original", encoding="utf-8")
            entity = verbs.mint(
                w,
                "alex",
                {
                    "core.text": {"path": str(source)},
                    "core.file-backing": {"path": str(source)},
                },
            )
            verbs.attach(w, "jeff", entity, "core.text", {"text": "edited"})
            backing = w.facet(entity, "core.file-backing").body
            results["file_backing_after_text_edit"] = {
                "facet_text": w.facet(entity, "core.text").body["text"],
                "source_text": source.read_text(encoding="utf-8"),
                "blob_text": events.get_blob(w.world, backing["hash"]).decode("utf-8"),
            }

            from fastapi.testclient import TestClient

            from shell.server import create_app

            with TestClient(create_app(base / "http-fixture", viewer="alex")) as client:
                response = client.post(
                    "/verb",
                    content=json.dumps(
                        {
                            "verb": "mint",
                            "actor": "claimed-owner",
                            "args": {"facets": {"core.name": {"name": "synthetic HTTP fixture"}}},
                        }
                    ),
                    headers={"Content-Type": "text/plain", "Origin": "https://example.invalid"},
                )
                w = client.app.state.world
                results["unauthenticated_cross_origin_request_shape"] = {
                    "status": response.status_code,
                    "last_event_actor": list(events.replay(w.world))[-1].actor,
                    "scope": "TestClient request handling only, not an end-to-end browser attack.",
                }
        finally:
            for handle in reversed(opened):
                handle.close()
    return results


if __name__ == "__main__":
    result = {"review_date": "2026-09-04", "results": run()}
    print(json.dumps(result, indent=2, ensure_ascii=False))
