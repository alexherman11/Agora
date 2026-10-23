"""World-owned verbs: ordinary inspectable notes, installed explicitly, never on import."""

NOTES = (
    (
        "task-next",
        '# task-next <task> "<next action>" "<acceptance>"\n'
        'read $1\ndo prop $1 next_action="$2" acceptance="$3" '
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) and $2 != "" and $3 != ""',
    ),
    (
        "task-revise",
        '# task-revise <task> "<goal>" "<acceptance>" <request-ref> "<next action>"\n'
        'read $1\ndo prop $1 goal="$2" acceptance="$3" request_ref="$4" next_action="$5" '
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) '
        'and $2 != "" and $3 != "" and $4 != "" and $5 != ""',
    ),
    (
        "task-review",
        '# task-review <task> <current-basis> "<next action>"\n'
        "# Read the result first. Review does not verify acceptance or finish a parent.\n"
        'read $1\ndo prop $1 reviewed_basis=$2 next_action="$3" remove=review_at '
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) and $2 != "" and $3 != ""',
    ),
    (
        "task-verify",
        "# task-verify <task> <current-basis> <evidence-note>\n"
        "# Inspect evidence against acceptance first. "
        "This is attributed owner verification, not host proof.\n"
        "# Invalidate first so re-attesting a swapped pointer cannot be a native no-op.\n"
        "# An interruption between the two writes leaves the task unverified.\n"
        "read $1\nread $3\n"
        'do prop $1 remove=verified_basis '
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) '
        'and $1.verified_basis != "" and $2 != "" and $3 != ""\n'
        "do prop $1 verified_basis=$2 verified_evidence=$3 "
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) and $2 != "" and $3 != ""',
    ),
    (
        "task-followup",
        "# task-followup <task> <ISO-datetime-with-timezone>\n"
        "# One-shot owner review, never permission, automatic resume or an external action.\n"
        'read $1\ndo prop $1 review_at="$2" '
        'when ($1.owner = $me or $1.lead = $me or $1.asked_by = $me) and $2 != ""',
    ),
)


def lines(surface):
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
