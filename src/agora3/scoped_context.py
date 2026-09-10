"""Declared action inputs and dependency checks under the native gateway lock."""

import json

from agora3.world import Refusal, identifier


def check_reads(reads):
    if not isinstance(reads, dict) or set(reads) - {"queries", "ids", "arg_ids"}:
        raise Refusal("reads accepts queries (arrays of facet names), ids and arg_ids.")
    for field in ("queries", "ids", "arg_ids"):
        value = reads.get(field, [])
        if not isinstance(value, list) or len(value) > 20:
            raise Refusal("Each reads field must be an array of at most 20 entries.")
        if field == "queries":
            for facets in value:
                if not isinstance(facets, list) or not 1 <= len(facets) <= 20:
                    raise Refusal("Each reads query needs 1–20 facet names (AND semantics).")
                for name in facets:
                    identifier(name)
        else:
            for name in value:
                identifier(name)


def scoped_snapshot(world, reads, args):
    check_reads(reads)
    requested = set(reads.get("ids", []))
    for name in reads.get("arg_ids", []):
        value = args.get(name)
        values = value if isinstance(value, list) else [value]
        if len(values) > 200:
            raise Refusal("An argument read list is limited to 200 object IDs.")
        for item in values:
            requested.add(identifier(item))
    queries = [{"facets": names, "items": []} for names in reads.get("queries", [])]
    objects, versions = [], {name: 0 for name in requested}
    with world.connection() as db:
        db.execute("BEGIN")
        watermark = db.execute("SELECT coalesce(max(seq),0) FROM events").fetchone()[0]
        for row in db.execute("SELECT body FROM objects ORDER BY id"):
            obj = json.loads(row[0])
            selected = obj["id"] in requested
            if selected:
                versions[obj["id"]] = obj["revision"]
            for query in queries:
                if all(facet in obj["facets"] for facet in query["facets"]):
                    query["items"].append([obj["id"], obj["revision"]])
                    selected = True
                    if len(query["items"]) > 1000:
                        raise Refusal(
                            "A declared input query exceeds 1000 objects; "
                            "narrow the action's reads."
                        )
            if selected:
                objects.append(obj)
                if len(objects) > 1000:
                    raise Refusal("Declared action inputs exceed 1000 objects; narrow the reads.")
    return {
        "items": objects,
        "watermark": watermark,
        "complete": True,
        "read_guards": {"objects": versions, "queries": queries},
        "missing_ids": [name for name, revision in versions.items() if revision == 0],
    }


def assert_reads(world, guards):
    """Call while holding the gateway's cross-process write lock, before committing."""
    if not guards["objects"] and not guards["queries"]:
        return
    actual_versions = {name: 0 for name in guards["objects"]}
    actual_queries = [[] for query in guards["queries"]]
    with world.connection() as db:
        db.execute("BEGIN")
        for row in db.execute("SELECT body FROM objects ORDER BY id"):
            obj = json.loads(row[0])
            if obj["id"] in actual_versions:
                actual_versions[obj["id"]] = obj["revision"]
            for index, query in enumerate(guards["queries"]):
                if all(facet in obj["facets"] for facet in query["facets"]):
                    actual_queries[index].append([obj["id"], obj["revision"]])
    if actual_versions != guards["objects"] or any(
        actual != query["items"]
        for actual, query in zip(actual_queries, guards["queries"], strict=True)
    ):
        changed = [
            name
            for name, revision in actual_versions.items()
            if revision != guards["objects"][name]
        ]
        changed += [
            "facets=" + ",".join(query["facets"])
            for actual, query in zip(actual_queries, guards["queries"], strict=True)
            if actual != query["items"]
        ]
        raise Refusal(
            "Declared action inputs changed ("
            + "; ".join(changed[:10])
            + "); read or invoke again. No proposed changes committed."
        )
