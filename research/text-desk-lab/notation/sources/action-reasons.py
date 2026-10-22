"""Reasons in one canonical duty group, including resolved and diagnostic evidence."""
from action_queue import REASON_FIELDS, snapshot

USAGE = "action-reasons:<recipient>:<policy>:<group-key>"
FIELDS = REASON_FIELDS
ARG = "needed"


def rows(desk, arg, session):
    return snapshot(desk, arg, reasons=True)
