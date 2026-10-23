# World policy payload for Ibis / JEFF — not applied

Keep eligibility in ordinary world props; no new world grammar or rule needed.
No task, corner, dependency rule, notice or historical event needs rewriting.
JEFF's notify_on_land correction is separate and unchanged.

First, after source review/approved deployment, ensure exactly zero notes match:

    find prop:role=task-transition-policy

If a note already exists, read it and reconcile rather than creating a duplicate.
On an ordinary surface JEFF owns (Corners shown here), stage disabled:

    look f185 :1
    do create f185 kind=note title="Task transition wake policy" role=task-transition-policy version=1 enabled=off states=ready,landed,failed,done milestones=completed,failed text="Only new actionable transitions call the task lead. Bare waiting and checkpoint rewording stay quiet. Explicit questions, human input, mentions and dependency clearance retain their own routes. Queue receipts are not model acknowledgements."

Retain the returned note identity as POLICY (placeholder below; do not paste
POLICY literally). Review the note and current source receipt before enabling:

    read POLICY
    do prop POLICY enabled=on

This is opt-in policy, not deployment approval. Existing inboxes and cursors
must not be cleared or rewound. On first opted-in pass the saved cursor still
governs which events are gathered; no historical replay is requested.
Existing pending/unknown provider deliveries must not be retried to "test" this.

Inverse, with no deletion or history rewrite:

    read POLICY
    do prop POLICY enabled=off

Absent/disabled/unsupported/ambiguous policy means legacy routing. Disabling
does not erase accumulated receipts or queued input. If code is subsequently
reversed, retain resident state and existing notices. Source reversal is the
inverse of candidate.patch ONLY on the reviewed outputs in manifest.json;
otherwise reconcile intervening changes rather than restoring whole files.

No world policy was created, enabled or disabled by this worker.
