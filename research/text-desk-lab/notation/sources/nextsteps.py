"""Inspect the same canonical attention projection the resident receives."""

import task_next_steps

USAGE = "nextsteps:<actor>"
FIELDS = task_next_steps.FIELDS
ARG = "needed"


def rows(desk, arg, session):
    return task_next_steps.rows(desk.world, arg)
