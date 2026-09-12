"""The native vocabulary for durable work, independent attempts and collaboration.
Never grant authority from a brief, status message or worker-authored object.
"""

from agora3.schemas import record

ID = {"type": "string", "minLength": 1, "maxLength": 160}
IDS = {"type": "array", "items": ID, "maxItems": 64, "uniqueItems": True}
TEXT = {"type": "string", "minLength": 1, "maxLength": 12000}
SCOPE = record(
    {name: IDS for name in ("read_objects", "write_objects", "read_packages", "write_packages")},
    [],
)


def spec(name, description, properties, required=None):
    return {"name": name, "description": description, "input_schema": record(properties, required)}


SPECS = [
    spec(
        "work.create",
        "Delegate a durable task to an independent Astra worker. A worker sees only granted "
        "objects/packages and edits its own candidate, never the live world. Use existing IDs "
        "or explicitly name new object/package IDs. Tasks get their own output prefix. "
        "resources lists exclusive resources held for this attempt; wait reasons are visible. "
        "No arbitrary guest/host execution or live UI control is granted. Can write browser or "
        "Python packages, build them and check Python actions in the clean yard. "
        "Completion returns a candidate and evidence, not installation. Use work.diff/adopt "
        "then ordinary build/install when adoption is justified. Independent tasks continue "
        "after this conversational turn ends. Do not use ambient spawn_agent.",
        {
            "title": {"type": "string", "minLength": 1, "maxLength": 140},
            "brief": TEXT,
            "scope": SCOPE,
            "resources": IDS,
            "depends_on": IDS,
            "collaborators": IDS,
            "priority": {"type": "integer", "minimum": 0, "maximum": 2},
            "max_calls": {"type": "integer", "minimum": 4, "maximum": 100},
            "timeout_seconds": {"type": "integer", "minimum": 30, "maximum": 1800},
            "notify": {"type": "boolean"},
        },
        ["title", "brief", "scope"],
    ),
    spec(
        "work.list",
        "Read tasks, actual attempt state, wait reasons and recent public progress.",
        {},
        [],
    ),
    spec(
        "work.inspect",
        "Read a task, scoped brief, messages, result and attempt history.",
        {"id": ID},
    ),
    spec(
        "work.diff", "Read the latest candidate's exact changes and baseline revisions.", {"id": ID}
    ),
    spec(
        "work.message",
        "Send task-relevant information to a worker, including while it is running. Recorded "
        "delivery distinguishes queued from runtime-accepted. This does not widen permissions "
        "or change the brief's acceptance criteria. Use work.revise for changed intent.",
        {"id": ID, "text": TEXT},
    ),
    spec(
        "work.revise",
        "Revise a task brief, stop its old attempt and queue a new attempt. Prior results remain "
        "inspectable but cannot be adopted under the new brief. Scope stays unchanged.",
        {"id": ID, "brief": TEXT, "expected_brief_revision": {"type": "integer"}},
    ),
    spec(
        "work.cancel",
        "Revoke further work for this task; retain committed candidate data.",
        {"id": ID},
    ),
    spec(
        "work.retry",
        "Explicitly retry a failed, blocked or interrupted task with unchanged scope.",
        {"id": ID},
    ),
    spec(
        "work.adopt",
        "Atomically adopt candidate object/source changes if the brief and all scoped baseline "
        "inputs are still current. Does not install packages or imply test success. Refuses "
        "stale inputs instead of merging silently; inspect and revise if needed.",
        {"id": ID, "expected_brief_revision": {"type": "integer"}},
    ),
    spec("work.resources", "Inspect worker capacity, resource holders and waiting tasks.", {}, []),
    spec(
        "work.link",
        "Allow two tasks to exchange messages and inspect each other's public progress/results. "
        "This deliberately shares those reports; it does not grant access to their world data.",
        {"left": ID, "right": ID},
    ),
]

WORKER_SPECS = [
    spec(
        "work.wait_messages",
        "Wait up to 30 seconds for new task messages; returns promptly on cancellation. "
        "Use the returned count as after_count on your next wait.",
        {
            "after_count": {"type": "integer", "minimum": 0, "maximum": 100},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 30},
        },
        [],
    ),
    spec(
        "work.self",
        "Read your exact brief, granted scope, baseline, messages and output prefix.",
        {},
        [],
    ),
    spec(
        "work.report",
        "Record concise public progress, evidence or a blocker; never private reasoning.",
        {"text": TEXT, "kind": {"enum": ["progress", "question", "blocked", "evidence"]}},
        ["text"],
    ),
    spec(
        "work.messages", "Read messages directed to your task, including mid-turn updates.", {}, []
    ),
    spec(
        "work.send",
        "Send a relevant report to an explicitly linked collaborator or to JEFF (id='jeff').",
        {"id": ID, "text": TEXT},
    ),
    spec("work.inspect", "Read a linked collaborator's public task status and result.", {"id": ID}),
    spec(
        "work.resources",
        "Inspect the named resource queue and your attempt's resource ownership.",
        {},
        [],
    ),
]
