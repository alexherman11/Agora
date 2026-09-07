"""The bounded declarative lens vocabulary, independent of any renderer.
Never: never executes source code, follows references, or grants data access."""

FIELDS = {"core.name.name", "core.text.text", "written_by", "revision"}


def validate(body: dict) -> None:
    if type(body.get("version")) is not int or body["version"] != 1:
        raise ValueError("core.lens version must be 1")
    source = body["source"]
    if set(source) - {"scene", "entities", "facet"} or ("scene" in source) == (
        "entities" in source
    ):
        raise ValueError("lens source needs exactly one of scene or entities, plus optional facet")
    if "scene" in source and not isinstance(source["scene"], str):
        raise ValueError("source.scene must be an entity reference")
    if "entities" in source and (
        not isinstance(source["entities"], list)
        or len(source["entities"]) > 200
        or not all(isinstance(e, str) for e in source["entities"])
    ):
        raise ValueError("source.entities must contain at most 200 entity references")
    if "facet" in source and not isinstance(source["facet"], str):
        raise ValueError("source.facet must be a facet type")
    listing, detail = body["list"], body["detail"]
    if set(listing) - {"component", "field", "secondary"} or listing.get("component") != "list":
        raise ValueError("list must be {component: list, field, secondary?: [field]}")
    if set(detail) != {"component", "field"} or detail["component"] != "text":
        raise ValueError("detail must be {component: text, field}")
    secondary = listing.get("secondary", [])
    if not isinstance(secondary, list) or len(secondary) > 2:
        raise ValueError("list.secondary must be at most two fields")
    for value in [listing.get("field"), detail.get("field"), *secondary]:
        if not isinstance(value, str) or value not in FIELDS:
            raise ValueError(f"lens fields must be one of {sorted(FIELDS)}")
    if body.get("density", "comfortable") not in ("compact", "comfortable"):
        raise ValueError("density must be compact or comfortable")
