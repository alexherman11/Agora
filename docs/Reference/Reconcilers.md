# Reconcilers

A reconciler is a useful pattern for keeping observed reality near retained
intent: a player stays paused, an export finishes, a service restarts, or a layout
continues admitting new items. It is not a required architecture for all activity.
A general controller scheduler is not implemented in the current runtime.

## Intent, observations and effects

Desired state, observed state and accepted actions mean different things. A
running process is not proof of a working application. Observations should identify
what was measured, when and by whom, with useful uncertainty and failure detail.
Several observers can legitimately disagree or describe different aspects. A
combined status needs an understandable resolver; one observer is not the only
possible source of truth about a resource.

Pure derived values, observations, one-shot actions, streams, transactions and
maintained effects can coexist in one application. A pure evaluator can consume
authorized observations, clock samples or model results without making hidden
effects part of a read. Lazy evaluation and bounded iterative computation remain
options. There is no compulsory subsystem for every internal function.

## Execution choices

Re-observe often enough to avoid acting on obsolete assumptions. A useful step
may be an atomic batch or part of a larger workflow, not the undefined smallest
possible action. Controllers can be orchestrated when dependencies demand it.
Workflow ordering does not itself grant authority; actual effects use current
authorization and relevant state checks.

Resources may have explicit ownership or coordination to prevent controllers
fighting. Single-writer status does not establish exclusive control of a physical
resource. Cancellation, budgets, retries and resumption depend on the activity's
contract. No general convergence from arbitrary external state is promised.

## Failures and recovery

An unfinished task can be pending, blocked, conflicted, unavailable or have an
uncertain external outcome. Compact diagnostics suit retryable races. Durable
competing intent may merit retained alternatives; every failure need not create
a conflict object. Do not turn a timeout into proof that an operation did not act.

Record enough to understand important accepted actions and recover safely.
Native replay does not repeat execution. Restoration uses current authority,
which may already authorize resumption. A fresh execution credential is not
necessarily a new human decision. External services and guest processes require
their own observed recovery and idempotency behavior.

## Directions to test

Try a cancellable import with progress, a coordinated stop/reconfigure operation,
and an external update whose response can be lost after acceptance. Compare a
simple activity implementation with a reusable controller or workflow tool.
Choose scheduling, persistence and worker topology from those observations.
