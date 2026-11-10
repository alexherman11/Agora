"""Read-only revision-bound passages; offsets use UTF-16 code units, as DOM/TextEdit do."""
from world import Refusal


def capture(desk, value):
    import lens_ir
    import scene
    if not isinstance(value, dict):
        raise Refusal("Select the source words again")
    item, rev, field = (value.get(k) for k in ("item", "rev", "field"))
    if not isinstance(item, str) or field not in ("text", "title") or type(rev) is not int:
        raise Refusal("These words have no exact source binding")
    if lens_ir.may_read(desk, item):
        raise Refusal("The source is unavailable")
    if scene._rev_of(desk.world, item) != rev:
        raise Refusal("The source changed; select the words again")
    text = scene._ctx_for(desk.world, item).get(field)
    start, end, quote = (value.get(k) for k in ("start", "end", "quote"))
    if not isinstance(text, str) or type(start) is not int or type(end) is not int or not isinstance(quote, str):
        raise Refusal("These words have no exact source range")
    raw = text.encode("utf-16-le")
    if not 0 <= start < end <= len(raw) // 2:
        raise Refusal("Select a nonempty source range")
    try:
        before, selected, after = (raw[:start * 2].decode("utf-16-le"),
                                   raw[start * 2:end * 2].decode("utf-16-le"),
                                   raw[end * 2:].decode("utf-16-le"))
    except UnicodeError:
        raise Refusal("The source range splits a character")
    if selected != quote:
        raise Refusal("The selected words differ from the source; select them again")
    context = {}
    supplied = value.get("context", {})
    if not isinstance(supplied, dict) or set(supplied) - {"item", "destination"}:
        raise Refusal("Unknown quote context")
    for key, binding in supplied.items():
        if not isinstance(binding, dict) or not isinstance(binding.get("item"), str):
            raise Refusal("Quote context needs an exact source")
        if lens_ir.may_read(desk, binding["item"]):
            raise Refusal("The quote context is unavailable")
        current = scene._rev_of(desk.world, binding["item"])
        if type(binding.get("rev")) is not int or current != binding["rev"]:
            raise Refusal("The quote context changed; prepare the quote again")
        context[key] = {"item": binding["item"], "rev": current}
    return {"item": item, "rev": rev, "field": field, "start": start, "end": end, "quote": quote,
            "before": " ".join(before.split()[-6:]), "after": " ".join(after.split()[:6]),
            "context": context, "label": scene._ctx_for(desk.world, item).get("title") or "Source"}
