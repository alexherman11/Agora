"""Canonical grouped duties; eligibility comes from the referenced world policy."""
from action_queue import GROUP_FIELDS, snapshot

USAGE = "actions:<recipient>:<policy>"
FIELDS = GROUP_FIELDS
ARG = "needed"


def rows(desk, arg, session):
    return snapshot(desk, arg)
