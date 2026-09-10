"""Bounded application-view data access through the existing native gateway.
Never expose generic management, guest execution or another view's state to a package.
"""

import copy

from agora3.world import Refusal, encoded


def projection(obj, allowed):
    return {
        **obj,
        "facets": {
            name: copy.deepcopy(value) for name, value in obj["facets"].items() if name in allowed
        },
    }


def request(gateway, actor, obj, method, args):
    view = obj["facets"]["agora.application-view"]
    subject, grant = view["subject"], view["grant"]
    if not isinstance(args, dict):
        raise Refusal("Application request arguments must be an object.")
    if method == "read":
        if set(args) - {"id"} or args.get("id", subject) != subject:
            raise Refusal("This view can read only its explicitly bound subject.")
        return projection(gateway.world.get(subject), grant["read_facets"])
    if method == "transact":
        if (
            set(args) != {"changes"}
            or not isinstance(args["changes"], list)
            or len(args["changes"]) != 1
        ):
            raise Refusal("A subject-bound view submits exactly one subject change.")
        change = args["changes"][0]
        if not isinstance(change, dict) or change.get("id") != subject:
            raise Refusal("This view can write only its explicitly bound subject.")
        facets = change.get("facets")
        if not isinstance(facets, dict) or not set(facets) <= set(grant["write_facets"]):
            raise Refusal("The change contains facets outside this view's write grant.")
        result = gateway.commit(actor, args["changes"], via=view["package"])
        return {
            **result,
            "items": [projection(row, grant["read_facets"]) for row in result["items"]],
        }
    if method == "state.get":
        if args:
            raise Refusal("state.get takes no arguments; state belongs to this view.")
        return {"state": copy.deepcopy(view["state"]), "revision": obj["revision"]}
    if method == "state.set":
        if set(args) != {"state"} or not isinstance(args["state"], dict):
            raise Refusal("state.set requires a state object.")
        if len(encoded(args["state"]).encode()) > 1000000:
            raise Refusal("Retained view state is limited to 1 MB.")
        updated = {**view, "state": args["state"]}
        result = gateway.commit(
            actor,
            [
                {
                    "id": obj["id"],
                    "expected_revision": obj["revision"],
                    "facets": {"agora.application-view": updated},
                }
            ],
            internal=True,
            via=view["package"],
        )
        return {"revision": result["items"][0]["revision"], "retained": True}
    raise Refusal("Application method is not admitted. Use read, transact, state.get or state.set.")
