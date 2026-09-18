# Trial 3: consequential redesign while retaining an extensible language

Turn the expedition app into a reservation and returns system. This is a redesign,
not three extra panels. Existing trial 2 seeds remain the reproducible fixture.
Each builder owns its own existing module and cases, and may replace/delete its
own legacy claims. No coordinator edits to builder code. You may read the OLD
trial 2 versions; do not read peer trial 3 implementations before initial freeze.

The PI supplies business requirements and the language only. Builders must agree
directly on any new shared addresses/commands via collaboration messages. Publish
the ports you own in your own planning/logistics/finance.ports.md. Record received
agreements there too. Avoid putting a hidden serial execution order in the design.

Planning builder (notes_builder): mission lifecycle, packing plan and a redesigned
operations workbench; active-mission amendments (issue additional supplies), close
only after all reservations returned, and aggregate status. Coordinate directly
with logistics and finance. You own task flow, not their data rules.

Logistics builder (tasks_builder): immutable issued-quantity snapshots, partial
returns, inventory conservation, repricing stock for FUTURE issues, and resource
controls. Newly added actions must not be able to edit/delete old issued facts or
fabricate stock through returns. Transition constraints can inspect before state.

Finance builder (library_builder): snapshot prices at issue, exact partial refunds
at original prices, charges/refunds for amendments, ledger and budget integrity,
useful live financial views. Co-create reservation records with logistics via
disjoint create effects at the SAME record id; neither builder may call the other.

## Required acceptance scenarios

1. Initial ridge dispatch consumes 2 radios +1 tent, costs 540 as before.
2. Change radio unit price from 120 to 200. Return ONE old radio: credit 120,
   never 200. An attempted return of more units than issued is atomic refusal.
3. Amend the dispatched ridge mission to issue one additional radio at 200:
   stock, new reservation, project debit and ledger join one transaction.
4. Return all remaining issued units; closing the mission succeeds only then.
   Total stock and project funds return to original values (ignoring explicit
   top-ups/restocks). Duplicate returns cannot mint inventory or money.
5. A brand-new unrelated editor action attempting to mutate/delete a prior
   reservation is rejected by transition rules, regardless of action name.
6. Two concurrent partial-return or amendment requests cannot over-return,
   oversell, or double-refund. A safe disjoint request should still work.
7. Program views must support the workflow; use generic widgets and data only.

Address disagreements are yours to resolve directly. If the LANGUAGE is missing
a GENERAL operation, report it; do not encode JS or ask the PI to stitch features.
There is no claim that this prototype is a secure sandbox or production accounting.
Preserve exactly the initial trial 2 fixtures and name new command ports clearly.
