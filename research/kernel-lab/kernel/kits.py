"""Definition-only kits. No transport, executable paths, authority or world data.

The portable JSON is a value: a caller reads it through look and carries it to
another door. Import validates the same closed schema as export, before minting.
"""
import json
import re

from .kernel import Refused

FIELDS = {
    "word": set("word aliases word_kind takes help may once sealed undo from bound steps steps_bound fence status "
                "acts_on needs".split()),
    "lens": set("name title text".split()),
    "style": set("name title text".split()),
    "rule": set("name title on on_entry do do_bound off of_kind by".split()),
    "kind": set("name title help fields needs extends value aliases has".split()),
    "widget": set("name title code style help".split()),
    "theme": set("name title text".split()),     # a theme is its JSON text (theme/model.py), wallpaper assets inline
}
REF = re.compile(r"(?<![\w])([a-z]{2,4}\d+)(?![\w])")
# Fields that are the definition's own data, not words that name other things: never scanned for references, never
# remapped (a theme's JSON says "base0D" and "#ff0000", which read like ids).
OPAQUE = {"theme": {"text"}}


def validate(bundle):
    def bad():
        raise Refused("not a definition-only kit (version 1); no data or authority may travel")
    if not isinstance(bundle, dict) or set(bundle) != {"version", "source", "group", "definitions", "kernel"}:
        bad()
    if bundle["version"] != 1 or not isinstance(bundle["source"], str) or not isinstance(bundle["group"], str):
        bad()
    if not re.fullmatch(r"[0-9a-f]{24}", bundle["source"]) or not REF.fullmatch(bundle["group"]):
        bad()
    defs, kernel = bundle["definitions"], bundle["kernel"]
    if not isinstance(defs, list) or len(defs) > 200 or not isinstance(kernel, dict):
        bad()
    seen = {bundle["group"]}
    for d in defs:
        if not isinstance(d, dict) or set(d) != {"id", "facts"} or not isinstance(d["id"], str):
            bad()
        if not REF.fullmatch(d["id"]) or d["id"] in seen:
            bad()
        seen.add(d["id"])
        a = d["facts"]
        if not isinstance(a, dict) or not isinstance(a.get("kind"), str) or a["kind"] not in FIELDS:
            bad()
        allowed = FIELDS[a['kind']] | {'kind'} | ({f for f in a if re.fullmatch(r'(label|help)\.[a-z][a-z0-9-]*', f)}
                                                  if a['kind'] == 'word' else set())
        if set(a) - allowed or any(not isinstance(v, str) for v in a.values()):
            bad()
        if a["kind"] == "word":
            from .dictionary import names as entry_names
            if not all(a.get(f) for f in ("word", "word_kind", "help", "from", "bound")):
                bad()
            if a["from"] != "verb" and not re.fullmatch(r"module:[a-z][a-z0-9_-]*", a["from"]):
                bad()
            if a["from"] == "verb" and not a.get("steps"):
                bad()
            if a["word_kind"] not in ("do", "see", "hear", "hold"):
                bad()
            if any(not n or n != n.lower() or re.search(r"[\s;=]", n)
                   for n in (a["word"], a["bound"], *a.get("aliases", "").split())):
                bad()
            for name in entry_names(a) | {a['bound']}:
                if not name or re.search(r'[\s;=$]', name):
                    bad()
                if '.' in name and not (a['from'].startswith('module:') and name.startswith(a['from'][7:] + '.')):
                    raise Refused('dotted names belong to the implementing module')
        elif a["kind"] in ("lens", "style", "kind", "theme") and not a.get("name"):
            bad()
        if a["kind"] in ("word", "kind"):
            # shapes are checked as strictly as verb, word-set and make check them: a shape this kernel can't read
            # would otherwise arrive and fail (kernel review C4, 28 Oct)
            from .kinds import parse, KIND_NAME
            try:
                parse(a.get("needs"))
                parse(a.get("has"))
            except Refused as exc:
                raise Refused(f"a {a['kind']} in this kit has a shape this kernel can't read: {exc}") from None
            names = (([a["acts_on"]] if a.get("acts_on") else []) + str(a.get("extends") or "").split()
                     + ([a["value"]] if a.get("value") else []) + str(a.get("aliases") or "").split())
            if any(not KIND_NAME.match(n.casefold()) for n in names):
                raise Refused(f"a {a['kind']} in this kit names a kind that isn't a kind name: {' '.join(names)}")
        if a["kind"] == "theme":
            # a stranger's theme is checked as strictly as one typed here: no scripts, no addresses, assets inline and small
            from theme.model import ThemeError, check_text
            try:
                check_text(a.get("text"))
            except ThemeError as exc:
                raise Refused("a theme in this kit is not accepted: " + str(exc)[:300]) from None
    if any(not isinstance(t, str) or not REF.fullmatch(t) or t in seen or not isinstance(w, str)
           for t, w in kernel.items()):
        bad()
    known = seen | set(kernel)
    for d in defs:
        for field, value in d["facts"].items():
            if field in OPAQUE.get(d["facts"]["kind"], ()):
                continue
            if any(t not in known for t in REF.findall(value)):
                raise Refused("a definition refers to data outside the kit; replace that reference with an argument")
    return bundle


def kit(k, actor, st, entry, tx, group, saw=None):
    source = st.target
    if k.state.get(source, "kind") not in ("group", "place"):
        raise Refused("kit needs a group or place")
    if not k.is_leader(actor.person, source):
        raise Refused("only a group's leaders may make its kit")
    chosen = {t for t, a in k.state.things.items() if a.get("kind") in FIELDS and not a.get("forgotten")
              and (a.get("lives") == source or source in k.groups_of(t))
              and a.get("from") != "kernel"}
    # A view or verb may use a module's place-wide dictionary entries. They are
    # definitions too; the module thing, its run command and its grants are not.
    pending = list(chosen)
    while pending:
        t = pending.pop()
        a = k.state.things[t]
        if k.shown(actor.person, t) is None:
            raise Refused("a definition is not visible to you; nothing was gathered")
        text = " ".join(str(a.get(f, "")) for f in FIELDS[a["kind"]] if f not in OPAQUE.get(a["kind"], ()))
        for e in k.entries():
            ea = k.entry(e)
            names = {ea.get("word", ""), ea.get("bound", "")} | set(ea.get("aliases", "").split())
            if ea.get("from", "").startswith("module:") and any(
                    n and re.search(r"(?<![\w.-])" + re.escape(n) + r"(?![\w.-])", text) for n in names):
                if e not in chosen:
                    chosen.add(e)
                    pending.append(e)
    definitions = []
    for t in sorted(chosen):
        a = k.state.things[t]
        facts = {f: v for f, v in a.items() if (f == 'kind' or f in FIELDS[a['kind']]
                 or f.startswith(('label.', 'help.'))) and f not in ('steps_bound', 'do_bound')}
        # The portable executable lines carry entry ids themselves, so there is
        # only one representation for a recipient to review or revise.
        for field in ('steps', 'do'):
            if a.get(field + '_bound'):
                facts[field] = a[field + '_bound']
        definitions.append({'id': t, 'facts': facts})
    kernel = {e: k.state.get(e, "bound") for e in k.entries() if k.state.get(e, "from") == "kernel"}
    used = set(REF.findall(json.dumps([{"id": d["id"], "facts": {f: v for f, v in d["facts"].items()
                                                                   if f not in OPAQUE.get(d["facts"]["kind"], ())}}
                                       for d in definitions]))) - chosen - {source}
    bundle = validate({"version": 1, "source": k.log.records[0]["digest"], "group": source,
                       "definitions": definitions, "kernel": {t: kernel[t] for t in used if t in kernel}})
    t = tx.mint()
    for f, v in {"kind": "kit", "name": st.kv.get("name", k.name(source)), "bundle": bundle,
                 "made_by": actor.id, f"in:{source}": len(k.log.records) + 1}.items():
        tx.set(t, f, v)
    if source != k.place and not k.state.get(source, "open"):
        tx.set(t, "sees", f"group:{source}")
    return {"text": f"ok kit {t} [r?] · {len(definitions)} definitions, no data"}


def take(k, actor, st, entry, tx, group, saw=None):
    if st.target:
        bundle = k.state.get(st.target, "bundle")
    else:
        try:
            bundle = json.loads(st.kv.get("bundle", ""))
        except (ValueError, TypeError):
            raise Refused("take [<kit>] [bundle=<portable JSON>] in=<group>") from None
    bundle = validate(bundle)
    mapping = {bundle["group"]: group}
    for old, bound in bundle["kernel"].items():
        eid = next((e for e in k.entries() if k.state.get(e, "from") == "kernel"
                    and k.state.get(e, "bound") == bound), None)
        if not eid:
            raise Refused(f"this kit needs the kernel word {bound}")
        mapping[old] = eid
    # Refuse local collisions before writing; a second take never hides words.
    names, named_definitions = set(), set()
    for d in bundle["definitions"]:
        a = d["facts"]
        if a["kind"] == "word":
            from .dictionary import names as entry_names
            for name in entry_names(a) | {a['bound']}:
                if name in names or k.find_entry(name, group):
                    raise Refused(f"{name} already answers here; take into another group")
                names.add(name)
        elif a["kind"] in ("lens", "style", "kind", "theme") and a.get("name"):
            if a["kind"] == "kind":
                # a kind taken from a kit is declared here, so it meets the same rules make does: never the kernel's
                # own kinds, leaders only when it has a shape, one per scope (kernel review round 2: a kit gave said a
                # shape)
                k.kinds.validate_decl(actor, {f: a[f] for f in ("name", "needs", "extends", "value", "aliases", "has")
                                              if f in a}, group)
            key = (a["kind"], a["name"])
            if key in named_definitions or any(k.state.get(t, "name") == a["name"] and group in k.groups_of(t)
                                               for t in k.things(a["kind"])):
                raise Refused(f"{a['name']} is already defined here")
            named_definitions.add(key)
    for d in bundle["definitions"]:
        mapping[d["id"]] = tx.mint()
    for d in bundle["definitions"]:
        t = mapping[d["id"]]
        for f, v in d["facts"].items():
            tx.set(t, f, v if f in OPAQUE.get(d["facts"]["kind"], ()) else REF.sub(lambda m: mapping[m[0]], v))
        tx.set(t, "origin", {"world": bundle["source"], "thing": d["id"]})
        tx.set(t, "made_by", actor.id)
        tx.set(t, f"in:{group}", len(k.log.records) + 1)
        if d["facts"]["kind"] == "word":
            tx.set(t, "lives", group)
        if d["facts"]["kind"] == "rule":
            # a taken rule runs as its taker, so it hears what they trust: by=maker unless the kit says anyone
            # (approved-builds review H1: a kit dropped by=, and the taken rule heard every member)
            from .words import _rule_by
            tx.set(t, "by", _rule_by(d["facts"].get("by") or "maker"))
        if group != k.place and not k.state.get(group, "open"):
            tx.set(t, "sees", f"group:{group}")
    return {"text": f"ok take [r?] · {len(bundle['definitions'])} new definitions in {k.name(group)}"}


def rename(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, "kind") != "word":
        raise Refused("rename needs a dictionary entry")
    home = k.state.get(t, "lives")
    if not k.is_leader(actor.person, home):
        raise Refused("only leaders of the entry's own group may rename it")
    values = {f: st.kv[f].lower() for f in ("word", "aliases") if f in st.kv}
    from .dictionary import check_names
    check_names(k, t, values)
    if not values or any(not re.fullmatch(r"[^\s;=]+", n) for v in values.values() for n in v.split()):
        raise Refused("rename <entry> word=<name> aliases=\"<names>\"")
    if "word" in values and len(values["word"].split()) != 1:
        raise Refused("a word needs one name")
    for n in (values.get("word", "") + " " + values.get("aliases", "")).split():
        other = k.find_entry(n, home)
        if other and other != t:
            raise Refused(f"{n} already answers here")
    k.fence(actor, t, list(values), saw)
    from .dictionary import bind_legacy
    bind_legacy(k, tx)
    for f, v in values.items():
        tx.set(t, f, v)
    return {"text": "ok rename [r?] · the bound name still answers"}


def module(k, actor, st, entry, tx, group, saw=None):
    name = st.words.strip()
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", name) or k.module_named(name):
        raise Refused("module needs a new plain name")
    try:
        run = json.loads(st.kv.get("run", ""))
    except ValueError:
        run = None
    if not isinstance(run, list) or not run or any(not isinstance(x, str) or not x for x in run):
        raise Refused("run= needs a JSON list of executable and arguments, supplied here by the steward")
    mid, grant = tx.mint(), tx.mint()
    for f, v in {"kind": "module", "name": name, "run": run, "publishes": name + ".*", "on": True}.items():
        tx.set(mid, f, v)
    for f, v in {"kind": "grant", "to": mid, "words": st.kv.get("grants", ""), "where": k.place,
                 "by": actor.person}.items():
        tx.set(grant, f, v)
    return {"text": f"ok module {name} [r?] · local run command and explicit grants"}


def grant(k, actor, st, entry, tx, group, saw=None):
    """One more grant to a module or widget already here; undo takes it back. Grants are never edited in place,
    so every widening is its own act with its own author."""
    m = st.target
    if k.state.get(m, "kind") not in ("module", "widget"):
        raise Refused("grant needs a module or widget")
    words = str(st.kv.get("words", "")).strip()
    if not words:
        raise Refused('grant needs words="<words>"')
    g = tx.mint()
    for f, v in {"kind": "grant", "to": m, "words": words, "where": k.place, "by": actor.person}.items():
        tx.set(g, f, v)
    if st.kv.get("only"):
        tx.set(g, "only", str(st.kv["only"]))
    return {"text": f"ok grant {k.name(m)} {words} [r?] · undo takes it back"}
