"""A bounded, non-executable render tree shared by preview, tests, and the browser.
Never: never evaluates markup, CSS expressions, source code, or world mutations."""

import re

TAGS = {"div", "span", "p", "button", "h1", "h2", "h3", "pre", "label", "input", "textarea"}
EVENTS = {
    "click",
    "pointerdown",
    "pointermove",
    "pointerup",
    "pointercancel",
    "keydown",
    "input",
    "change",
}
STYLES = {
    "background",
    "borderColor",
    "borderWidth",
    "borderStyle",
    "boxSizing",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "marginTop",
    "marginRight",
    "marginBottom",
    "marginLeft",
    "flex",
    "flexGrow",
    "flexShrink",
    "flexBasis",
    "alignSelf",
    "order",
    "textOverflow",
    "wordBreak",
    "overflowWrap",
    "letterSpacing",
    "textDecoration",
    "transition",
    "outline",
    "outlineOffset",
    "display",
    "position",
    "left",
    "top",
    "right",
    "bottom",
    "width",
    "height",
    "minWidth",
    "minHeight",
    "maxWidth",
    "maxHeight",
    "padding",
    "margin",
    "gap",
    "border",
    "borderRadius",
    "backgroundColor",
    "color",
    "fontSize",
    "fontWeight",
    "fontFamily",
    "lineHeight",
    "whiteSpace",
    "overflow",
    "cursor",
    "userSelect",
    "touchAction",
    "flexDirection",
    "flexWrap",
    "alignItems",
    "justifyContent",
    "gridTemplateColumns",
    "boxShadow",
    "opacity",
    "zIndex",
    "textAlign",
    "transform",
}
SAFE_STYLE = re.compile(r"^[a-zA-Z0-9 #.,%()+\-/'\"]{0,160}$")


def validate(tree):
    nodes = {}

    def visit(node, depth):
        if depth > 20 or len(nodes) >= 500 or not isinstance(node, dict):
            raise ValueError("render tree exceeds depth/node limits or has a non-object node")
        if set(node) - {"id", "tag", "text", "value", "style", "on", "children", "entity", "label"}:
            raise ValueError(
                "tree nodes allow id, tag, text, value, style, on, children, entity, label"
            )
        key = node.get("id")
        if not isinstance(key, str) or not key or len(key) > 120 or key in nodes:
            raise ValueError("every render node needs a unique id of at most 120 characters")
        if node.get("tag") not in TAGS:
            raise ValueError(f"unsupported render tag; choose from {sorted(TAGS)}")
        for field in ("text", "value", "label", "entity"):
            if field in node and (not isinstance(node[field], str) or len(node[field]) > 32_000):
                raise ValueError(f"node {field} must be bounded text")
        style, handlers = node.get("style", {}), node.get("on", {})
        if not isinstance(style, dict):
            raise ValueError("style must be an object mapping CSS properties to string values")
        if set(style) - STYLES:
            raise ValueError(
                f"unsupported style properties {sorted(set(style) - STYLES)}; "
                f"allowed: {sorted(STYLES)}"
            )
        for prop, value in style.items():
            if (
                not isinstance(value, str)
                or not SAFE_STYLE.fullmatch(value)
                or any(
                    word in value.lower()
                    for word in ("url", "expression", "fixed", "sticky", "var(", "attr(")
                )
            ):
                raise ValueError(f"unsafe style value for {prop}")
        if (
            not isinstance(handlers, dict)
            or set(handlers) - EVENTS
            or not all(isinstance(v, str) and len(v) <= 80 for v in handlers.values())
        ):
            raise ValueError("event handlers must be bounded names for supported input events")
        nodes[key] = node
        children = node.get("children", [])
        if not isinstance(children, list):
            raise ValueError("children must be a list")
        for child in children:
            visit(child, depth + 1)

    visit(tree, 0)
    return nodes
