"""The public command vocabulary, shared by tool derivation and clients.
Never: never executes commands or maintains an independent JEFF tool list."""

from kernel.schema import Param, VerbDef


def _verb(name: str, doc: str, **params: tuple[str, bool, str]) -> VerbDef:
    return VerbDef(name, doc, {k: Param(*v) for k, v in params.items()})


_ENTITY = ("str", True, "the entity id")
REGISTRY: tuple[VerbDef, ...] = (
    _verb(
        "open_component_candidate",
        "Open an interactive, isolated preview. Expires after five idle minutes.",
        entity=_ENTITY,
        revision=("int", False, "source revision"),
        viewport=("dict", False, "{width,height}"),
    ),
    _verb(
        "candidate_event",
        "Interact with an isolated candidate; never changes the live world.",
        candidate=("str", True, "candidate handle"),
        event=("dict", True, "{node,type,...}"),
        fingerprint=("str", True, "last candidate frame fingerprint"),
        local=("dict", False, "last local state"),
        viewport=("dict", False, "{width,height}"),
    ),
    _verb(
        "close_component_candidate",
        "Close and discard an interactive candidate.",
        candidate=("str", True, "candidate handle"),
    ),
    _verb(
        "component_view",
        "Render active or candidate executable component; returns tree and input fingerprint.",
        entity=("str", False, "component ref; omit for current display"),
        revision=("int", False, "source revision"),
        local=("dict", False, "transient interaction state"),
        viewport=("dict", False, "{width,height}"),
    ),
    _verb(
        "test_component",
        "Run 1–24 interaction cases in a disposable world. "
        "Passing records a receipt; failure changes nothing live.",
        entity=_ENTITY,
        cases=(
            "list",
            True,
            "[{event:{node,type,...},expect:{text_contains?,state?,effect_count?,"
            "placement?,node?,value?}}]; or action/args instead of event",
        ),
        revision=("int", False, "exact candidate source revision"),
    ),
    _verb(
        "activate_component",
        "Activate an exact tested component revision; supports admitted-version restoration.",
        entity=_ENTITY,
        revision=("int", True, "exact source revision"),
        expected_revision=("int", True, "current core.display revision; 0 if absent"),
    ),
    _verb(
        "component_event",
        "Deliver an input event to a rendered handler with scoped effects.",
        entity=_ENTITY,
        revision=("int", True, "active source revision"),
        event=("dict", True, "{node,type,x?,y?,key?,value?}"),
        fingerprint=("str", True, "from component_view"),
        local=("dict", False, "transient interaction state"),
        viewport=("dict", False, "{width,height}"),
    ),
    _verb("component_actions", "Discover active extension actions and parameter schemas."),
    _verb(
        "invoke_component",
        "Invoke a named action on an admitted, active component.",
        entity=_ENTITY,
        revision=("int", True, "active source revision"),
        action=("str", True, "manifest action name"),
        args=("dict", True, "action arguments"),
    ),
    _verb(
        "mint",
        "Bring a new entity into the world, optionally with initial facets. Returns its id.",
        facets=("dict", False, "{facet_type: body} to attach at birth"),
    ),
    _verb(
        "attach",
        "Attach a facet to an entity, or update the one it has.",
        entity=_ENTITY,
        facet_type=("str", True, "one of the known facet types"),
        body=("dict", True, "the facet body, in that type's shape"),
        expected_revision=("int", False, "reject a stale edit; 0 requires an absent facet"),
    ),
    _verb(
        "read",
        "Read an entity's facets at full fidelity.",
        entity=_ENTITY,
        facet_type=("str", False, "read only this facet type"),
        revision=("int", False, "read a retained revision of the specified facet"),
    ),
    _verb(
        "place",
        "Place an entity on the desk (or another scene).",
        entity=_ENTITY,
        mode=("str", False, "icon | summary | full (default icon)"),
        transform=("dict", False, "{x, y, scale}; missing keys default"),
        scene=("str", False, "scene id; defaults to the desk"),
    ),
    _verb(
        "preview_lens",
        "Preview a declarative lens before activation; reads only its bound source.",
        entity=_ENTITY,
        revision=("int", False, "retained definition revision"),
        selected=("str", False, "selected entity within the lens source"),
        offset=("int", False, "page offset; each page has up to 100 rows"),
    ),
    _verb(
        "activate_lens",
        "Activate a previewed lens revision; empty entity restores the default desk.",
        entity=("str", False, "lens entity, or empty for default"),
        revision=("int", False, "definition revision; defaults to current"),
        expected_revision=("int", False, "current core.display revision; 0 if absent"),
    ),
)
