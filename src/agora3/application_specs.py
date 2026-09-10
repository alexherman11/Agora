"""Native application management and scoped view transport schemas.
Never hand a package the management authority used to open its view.
"""

from agora3.schemas import record


def specs():
    text = {"type": "string"}
    revision = {"type": "integer", "minimum": 0}
    bounds = record(
        {
            key: {"type": "number", "minimum": -10000, "maximum": 10000}
            for key in ("x", "y", "width", "height")
        }
    )
    definitions = [
        ("list", "Discover installed applications and retained open/closed views.", {}, None),
        (
            "open",
            "Open an installed application on one explicit subject, or create from its defaults.",
            {"package": text, "subject": text, "bounds": bounds},
            ["package"],
        ),
        (
            "surface",
            "Read one view's pinned browser artifact and scoped context; no credentials.",
            {"view": text},
            None,
        ),
        (
            "request",
            "Invoke a view's bounded data/state API. "
            "The lease and scope are checked on every request.",
            {"view": text, "lease": text, "method": text, "args": {"type": "object"}},
            None,
        ),
        (
            "position",
            "Persist one appearance's bounds without changing its subject.",
            {"view": text, "bounds": bounds},
            None,
        ),
        (
            "close",
            "Close a view after its host has flushed edits/drafts; retain content and view state.",
            {"view": text},
            None,
        ),
        (
            "reopen",
            "Reopen a retained view with its existing state and grant.",
            {"view": text},
            None,
        ),
        (
            "refresh",
            "Adopt an installed update for one flushed view without widening its grant.",
            {"view": text},
            None,
        ),
        (
            "uninstall",
            "Disable an application and close its flushed views; "
            "retain documents, schemas and drafts.",
            {"package": text, "expected_revision": revision},
            None,
        ),
        (
            "export",
            "Export installed application source and schema requirements, "
            "excluding all user data/state.",
            {"package": text},
            None,
        ),
        (
            "import",
            "Validate, save, build and install a browser application bundle. "
            "Existing source needs an exact revision.",
            {"bundle": {"type": "object"}, "expected_revision": revision},
            ["bundle"],
        ),
    ]
    return [
        {
            "name": "application." + name,
            "description": description,
            "input_schema": record(properties, required),
        }
        for name, description, properties, required in definitions
    ]
