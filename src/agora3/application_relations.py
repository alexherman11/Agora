"""Bounded related-object access for declared subject-linked collections.
Never allow a relation to change its subject or expose other object facets.
"""

import copy

from agora3.world import Refusal


def related(gateway, actor, view, method, args):
    name = args.get("relation")
    rule = view["grant"].get("relations", {}).get(name)
    if not rule:
        raise Refusal("This view has no grant for that related collection.")
    facet, field, subject = rule["facet"], rule["subject_field"], view["subject"]
    page = gateway.world.query([facet], 1000)
    if not page["complete"]:
        raise Refusal("Related collection exceeds this prototype's bounded scan.")
    rows = {
        obj["id"]: obj
        for obj in page["items"]
        if not obj["id"].startswith("agora.") and obj["facets"][facet].get(field) == subject
    }

    def project(obj):
        return {**obj, "facets": {facet: copy.deepcopy(obj["facets"][facet])}}

    if method == "related.query" and set(args) == {"relation"}:
        return {"items": [project(obj) for obj in rows.values()], "complete": True}
    if method != "related.transact" or not rule["write"]:
        raise Refusal("This related collection does not admit that operation.")
    if set(args) - {"relation", "changes", "subject_revision"}:
        raise Refusal("Related writes require relation, changes and optional subject_revision.")
    changes = args.get("changes")
    if not isinstance(changes, list) or len(changes) != 1 or not isinstance(changes[0], dict):
        raise Refusal("Submit one revision-checked related-object change.")
    change = changes[0]
    oid, patch = change.get("id"), change.get("facets")
    if not isinstance(oid, str) or oid.startswith("agora."):
        raise Refusal("A related object must have an ordinary native object ID.")
    if not isinstance(patch, dict) or set(patch) != {facet}:
        raise Refusal("A related write can change only its declared linking facet.")
    value = patch[facet]
    if not isinstance(value, dict) or value.get(field) != subject:
        raise Refusal("A related object must retain its link to this view's subject.")
    if oid not in rows:
        try:
            gateway.world.get(oid)
        except Refusal:
            pass
        else:
            raise Refusal("The requested object does not belong to this subject's collection.")
        if len(rows) >= rule["max_items"]:
            raise Refusal("This subject's related collection has reached its item limit.")
    guards = None
    if "subject_revision" in args:
        revision = args["subject_revision"]
        if type(revision) is not int or revision < 1:
            raise Refusal("subject_revision must be a positive native revision.")
        guards = {subject: revision}
    result = gateway.commit(actor, changes, guards=guards, via=view["package"])
    return {**result, "items": [project(obj) for obj in result["items"]]}
