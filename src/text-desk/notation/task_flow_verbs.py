"""Editable world-verb seed texts; importing this module performs no world writes.

Install as ordinary on=house verb notes through the native gateway. The world's
notes, not these defaults, own subsequent customization. Guards are the existing
generic expression guards; every state transition is one native prop mutation.
"""

NOTES = (
    (
        "assign-task",
        "# assign-task <task> <owner>: ask one resident to own this task.\n"
        "# Delivery is a knock receipt, not acceptance. The owner accepts explicitly.\n"
        "read $1\n"
        "do prop $1 owner=$2 lead=$me asked_by=$me status=asked "
        "remove=accepted_by,blocked_on,blocker_owner,resume_when "
        'when $2 != ""',
    ),
    (
        "accept-task",
        "# accept-task <task>: its named owner explicitly accepts responsibility.\n"
        "# Another caller is skipped by the owner guard; nothing is accepted for them.\n"
        "read $1\n"
        "do prop $1 accepted_by=$me status=doing when $1.owner = $me",
    ),
    (
        "block-task",
        '# block-task <task> "<blocker>" <resolver> "<resume event>": record a wait.\n'
        "# All fields are required; a missing or empty field changes no task state.\n"
        "read $1\n"
        'do prop $1 status=blocked blocked_on="$2" blocker_owner="$3" resume_when="$4" '
        'when $2 != "" and $3 != "" and $4 != ""',
    ),
    (
        "worker-update",
        '# worker-update <task> <milestone> "<short summary>" "<evidence link>": '
        "send a material update.\n"
        "# Milestone: checkpoint, completed, failed, blocked. Lead with outcome/blocker, "
        "importance, next action.\n"
        "# Keep summary under 600 characters; retain full details on the task or evidence "
        "link. Routine progress needs no update.\n"
        "read $1\n"
        'do prop $1 worker_milestone=$2 worker_summary="$3" worker_evidence="$4" '
        'when ($2 = "checkpoint" or $2 = "completed" or $2 = "failed" or $2 = "blocked") '
        'and $3 != "" and $4 != ""',
    ),
    (
        "yield-work",
        "# yield-work <commission>: yield capacity; automatically eligible when a slot returns.\n"
        "# This differs from commission=paused, which requires an explicit resume.\n"
        "read $1\n"
        "do prop $1 commission=yielded",
    ),
)


def lines(surface):
    """Generate native creation commands; caller checks name conflicts before installing."""
    result = []
    for name, source in NOTES:
        body = (
            source.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("$", "\\$")
            .replace("\n", "\\n")
        )
        result.append(
            f'do create {surface} kind=note title={name} tags=verb on=house text="{body}"'
        )
    return result
