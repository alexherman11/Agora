"""Activate a panel in a typed version-1 partition; literals stay data."""
import json


def activate(raw, panel):
    tree = json.loads(raw)
    if not isinstance(tree, dict) or type(tree.get("v")) is not int or tree["v"] != 1 or "root" not in tree:
        raise ValueError("tree-activate needs partition version 1")
    seen, changed, count = set(), False, 0

    def ref(value):
        if not isinstance(value, dict) or set(value) != {"$ref"} or not isinstance(value["$ref"], str) or not value["$ref"]:
            raise ValueError("tree-activate needs typed panel references")
        return value["$ref"]

    def visit(node, depth=0):
        nonlocal changed, count
        count += 1
        if depth > 32 or count > 512 or not isinstance(node, dict):
            raise ValueError("tree-activate malformed or oversized partition")
        if "id" in node:
            ident = ref(node["id"])
            if ident in seen or "kids" in node or "axis" in node:
                raise ValueError("tree-activate duplicate or ambiguous leaf")
            seen.add(ident)
            return ident == panel
        if node.get("axis") not in ("x", "y", "tabs") or not isinstance(node.get("kids"), list) or not node["kids"]:
            raise ValueError("tree-activate malformed split")
        hits = [visit(k, depth + 1) for k in node["kids"]]
        if node["axis"] == "tabs":
            current = ref(node.get("active"))
            if any(hits) and current != panel:
                node["active"] = {"$ref": panel}
                changed = True
        else:
            weights = node.get("weights")
            if (not isinstance(weights, list) or len(weights) != len(node["kids"]) or
                    any(type(w) not in (int, float) or not 0 < w < float("inf") for w in weights)):
                raise ValueError("tree-activate malformed weights")
        return any(hits)

    if tree.get("root") is not None:
        visit(tree["root"])
    return json.dumps(tree, ensure_ascii=False, separators=(",", ":")) if changed else raw
