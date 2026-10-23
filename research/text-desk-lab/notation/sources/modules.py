"""modules:<note>: typed compositions through existing rows and pictures.

Reviewed adapter only. Current source ABI supplies a mutable Desk, but none is
passed to modules. This bridge observes input and returns rows; it has no effects.
"""

import json

from capability_modules import ContractError, Evidence, evaluate, fingerprint, plain
from module_examples import ROWS, registry
from world import Refusal

USAGE = "modules[:<note>[/trace]]"
FIELDS = ("item", "key", "title", "summary", "detail", "picture", "status", "revision")
ARG = "optional"
_REGISTRY = registry()


def rows(desk, arg, session):
    import scene

    if not arg:
        return [
            dict(
                item="",
                key=d["module"],
                title=d["module"],
                summary=d["input"] + " -> " + d["output"],
                detail=json.dumps(d, sort_keys=True),
                picture="",
                status="ready",
                revision=d["pin"],
            )
            for d in _REGISTRY.describe()
        ]
    trace_requested = arg.endswith("/trace")
    if trace_requested:
        arg = arg[:-6]
    title, item = "Module unavailable", arg
    try:
        item = desk._resolve(arg)
        subject = desk.world.subjects.get(desk.world.subject_of(item))
        if subject is None:
            raise ContractError("module definition must be a note")
        title = subject["title"]
        raw = subject.get("text", "")
        if len(raw.encode()) > 100_000:
            raise ContractError("module note exceeds 100,000 bytes")
        config = json.loads(raw)
        if not isinstance(config, dict) or not {"plan", "input"} <= set(config):
            raise ContractError("module note requires plan and input")
        if set(config) - {"plan", "input", "source", "into", "fields", "state"}:
            raise ContractError("unsupported module configuration field")
        prepared = _REGISTRY.prepare(config["plan"])
        if prepared.nodes[prepared.root].definition.output.identity != ROWS.identity:
            raise ContractError(
                "this row adapter requires rows.v1; computation ports are not row renderers"
            )
        evidence = [Evidence("configuration", fingerprint(config), config.get("state", "ready"))]
        value = config["input"]
        if "source" in config:
            source = config["source"]
            if not isinstance(source, str) or scene.source_head(source) in ("modules", "charts"):
                raise ContractError("source must be a non-composing row source")
            source_rows = scene.rows(desk, source, session)
            # Legacy rows carry no producer-health contract. Neither [] nor None
            # is permission to synthesize a fresh measurement of zero.
            status = "ready" if source_rows else "unknown"
            note = (
                ""
                if source_rows
                else "No source observations; empty and unavailable "
                "cannot be distinguished by the row contract."
            )
            evidence.append(Evidence(source, fingerprint(source_rows), status, note))
            fields = config.get("fields")
            into = config.get("into")
            if not isinstance(into, str) or not into:
                raise ContractError("source requires an explicit input field: into")
            if fields is not None and (
                not isinstance(fields, dict) or not all(isinstance(v, str) for v in fields.values())
            ):
                raise ContractError("source fields must map input words to source words")
            if not isinstance(value, dict):
                raise ContractError("source input must be an object")
            records = (
                [{k: row.get(v) for k, v in fields.items()} for row in source_rows or []]
                if fields is not None
                else source_rows or []
            )
            value = {**value, into: records}
        result = evaluate(prepared, value, evidence)
        revision = fingerprint(
            [result.interpretation, plain(value), [vars(e) for e in result.observations]]
        )
        if trace_requested:
            traces = []

            def walk(trace, path):
                traces.append(
                    dict(
                        item=item,
                        key=path,
                        title=trace.module,
                        summary=trace.status,
                        detail=json.dumps(
                            dict(
                                node=trace.node,
                                pin=trace.pin,
                                input=trace.input_revision,
                                output=trace.output_revision,
                                detail=trace.detail,
                            ),
                            sort_keys=True,
                        ),
                        picture="",
                        status=trace.status,
                        revision=revision,
                    )
                )
                for n, child in enumerate(trace.children):
                    walk(child, f"{path}.{n}")

            if result.trace is not None:
                walk(result.trace, "root")
            for n, observation in enumerate(result.observations):
                traces.append(
                    dict(
                        item=item,
                        key=f"observation.{n}",
                        title=observation.source,
                        summary=observation.status,
                        detail=observation.detail,
                        picture="",
                        status=observation.status,
                        revision=observation.revision,
                    )
                )
            return traces
        if result.result.value is None:
            return [
                dict(
                    item=item,
                    key="observation",
                    title=title,
                    summary="Module " + result.result.status,
                    detail=result.result.detail,
                    picture="",
                    status=result.result.status,
                    revision=revision,
                )
            ]
        output = plain(result.result.value)
        for row in output:
            row.update(item=item, revision=revision)
            # Retained stale data must never render as fresh because a leaf said ready.
            if result.result.status in ("stale", "unknown", "error", "partial"):
                row["status"] = result.result.status
                row["summary"] = result.result.status.capitalize() + ": " + row["summary"]
        return output
    except (ContractError, ValueError, TypeError, KeyError, Refusal) as exc:
        return [
            dict(
                item=item,
                key="error",
                title=title,
                summary="Module unavailable",
                detail=str(exc)[:2000],
                picture="",
                status="error",
                revision="",
            )
        ]
