"""Observation accounting only; the replay/checker continues independently."""


VERSION = 2
REPORT_WORDS = "log-world report"


def self_record(rec):
    # Older house-start full checks projected status inside their outer command.
    return rec.get("by") == "house" and rec.get("words") in (REPORT_WORDS, "log-world check")


def reconcile(reports, own_sequences, known_sequences=None):
    """Use recorded counter deltas, not invented historical monotonic readings.

    Only intervals between independent endpoints, <=60 seconds apart, already
    credited by the old checker survive. A self endpoint cannot bridge idle time.
    Missing history is left contaminated/unavailable, never silently reset.
    """
    if not reports:
        return 0.0, 0, None
    last = reports[-1]
    if last.get("counting_version") == VERSION:
        return last["observed_seconds"], last["observed_records"], last.get("accounting_correction")
    seconds, records, old_seconds, old_records = 0.0, 0, 0.0, 0
    anchor = None
    unknown = None
    removed_self = 0
    for row in reports:
        sec, count = row["observed_seconds"], row["observed_records"]
        ds, dc = sec - old_seconds, count - old_records
        if dc not in (0, 1) or ds < 0:
            unknown = "receipt prefix/counter discontinuity; historical contribution cannot be classified"
        if dc and known_sequences is not None and row["records"] not in known_sequences:
            unknown = "receipt endpoint missing from log metadata; historical contribution cannot be classified"
        eligible = dc == 1 and row["records"] not in own_sequences and row["state"] == "in-step"
        if dc and row["records"] in own_sequences:
            removed_self += dc
        if row["state"] != "in-step":
            anchor = None
        elif eligible:
            records += 1
            if anchor is not None:
                at, credited = anchor
                elapsed, contribution = row["at"] - at, sec - credited
                if 0 <= elapsed <= 60 and 0 <= contribution <= elapsed + 1:
                    # The old counter must have credited the entire interval.
                    # A restart/unavailable gap breaks that continuity.
                    if abs(contribution - elapsed) <= 1:
                        seconds += contribution
            anchor = (row["at"], sec)
        old_seconds, old_records = sec, count
    correction = {
        "version": VERSION, "status": "unavailable" if unknown else "reconciled",
        "reason": unknown or "self endpoints and intervals sustained only by self endpoints removed",
        "prior_records": last["observed_records"], "prior_seconds": last["observed_seconds"],
        "removed_self_records": removed_self,
        "removed_seconds": max(0.0, last["observed_seconds"] - seconds),
    }
    if unknown:
        return last["observed_seconds"], last["observed_records"], correction
    return seconds, records, correction
